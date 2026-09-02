"""
Advanced OCR Engine for Tell Tims Receipt Photos
Optimized for Tim Hortons receipt format:
XXXX-XXXX-XXXX-XXXX-XXXXX (20-21 digits)
"""

import re
import os
import io
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    try:
        import numpy as np
    except ImportError:
        np = None

def extract_digits_pattern(text):
    """
    Regex parser specifically tuned for Tim Hortons Survey Codes:
    e.g. 2032-9620-2142-1050-60409 (5 blocks of 4-5 digits)
    """
    if not text:
        return []

    found = []

    # 1. Match standard hyphen/space separated Tim Hortons pattern
    pattern1 = re.findall(r'(\d{4}[\s\-\.]\d{4}[\s\-\.]\d{4}[\s\-\.]\d{4}[\s\-\.]\d{4,5})', text)
    for p in pattern1:
        c = re.sub(r'[^0-9]', '', p)
        if 20 <= len(c) <= 21:
            found.append(c)

    # 2. Match continuous 20-21 digits
    pattern2 = re.findall(r'\b(\d{20,21})\b', text)
    for c in pattern2:
        found.append(c)

    # 3. Match near "Survey Code" keyword
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in ["survey code", "survey", "telltims"]):
            snippet = " ".join(lines[i:min(len(lines), i+4)])
            digits = re.sub(r'[^0-9]', '', snippet)
            for m in re.finditer(r'(\d{20,21})', digits):
                found.append(m.group(1))

    # Deduplicate while preserving order
    unique = []
    for f in found:
        if f not in unique:
            unique.append(f)
    return unique

clean_and_extract_codes = extract_digits_pattern


def preprocess_image_variants(img_bytes):
    """
    Generates optimized image filters using PIL & OpenCV if available
    """
    variants = []
    try:
        pil_img = Image.open(io.BytesIO(img_bytes))
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        variants.append(pil_img)

        # Grayscale & High Contrast
        gray = pil_img.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.2)
        variants.append(enhanced)

        # Sharpened
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        variants.append(sharpened)

        # If CV2 is available, add adaptive thresholding
        if HAS_CV2 and np is not None:
            np_img = np.array(gray)
            thresh = cv2.adaptiveThreshold(
                np_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
            )
            variants.append(Image.fromarray(thresh))
            _, otsu = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            variants.append(Image.fromarray(otsu))
    except Exception as e:
        print(f"[-] Preprocessing error: {e}")
        
    return variants


def extract_code_from_image_bytes(img_bytes):
    """
    Multi-stage OCR with smart fallback
    """
    variants = preprocess_image_variants(img_bytes)

    # 1. Try EasyOCR
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        for var_img in variants:
            np_arr = np.array(var_img)
            res = reader.readtext(np_arr, detail=0)
            full_text = " ".join(res)
            codes = extract_digits_pattern(full_text)
            if codes:
                return codes
    except Exception:
        pass

    # 2. Try Pytesseract
    try:
        import pytesseract
        for var_img in variants:
            text = pytesseract.image_to_string(var_img, config='--psm 6')
            codes = extract_digits_pattern(text)
            if codes:
                return codes
            text_gen = pytesseract.image_to_string(var_img)
            codes = extract_digits_pattern(text_gen)
            if codes:
                return codes
    except Exception:
        pass

    # 3. Try Online Cloud OCR Fallback
    try:
        import requests
        resp = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename': ('receipt.jpg', img_bytes, 'image/jpeg')},
            data={'apikey': 'helloworld', 'language': 'eng', 'OCREngine': '2'},
            timeout=15
        )
        if resp.status_code == 200:
            res_json = resp.json()
            parsed = res_json.get('ParsedResults', [])
            if parsed:
                codes = extract_digits_pattern(parsed[0].get('ParsedText', ''))
                if codes:
                    return codes
    except Exception:
        pass

    return []
