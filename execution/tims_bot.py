#!/usr/bin/env python3
"""
Tell Tims (Tim Hortons / Qualtrics) Smart Auto-Solver
Intelligent AI heuristics to automatically answer any survey question naturally and achieve 100% completion
"""

import sys
import os
import re
import json
import time
import random
import requests

POSITIVE_REVIEWS = [
    "Great experience! The coffee was piping hot, fresh and made to perfection.",
    "Very fast and friendly service at the counter. Food was fresh and delicious!",
    "Clean store, courteous staff, and my order was ready in under a minute.",
    "The drive-thru team was wonderful and very cheerful this morning. Great start to the day!",
    "Exceptional customer service, warm breakfast sandwich and great tasting coffee as always.",
    "Order was 100% accurate and served fresh. Love this Tim Hortons location!",
    "Quick service, friendly cashier, and great tasting fresh baked goods."
]

class SmartQuestionSolver:
    """
    Intelligent NLP & Heuristic engine to answer any Qualtrics survey question
    """
    @staticmethod
    def get_text_answer(qtext):
        qtext_lower = qtext.lower()
        if any(w in qtext_lower for w in ["enjoy", "like", "positive", "experience", "feedback", "comment", "tell us"]):
            return random.choice(POSITIVE_REVIEWS)
        if "name" in qtext_lower and "team" in qtext_lower:
            return "Alex"
        return ""

    @staticmethod
    def select_best_choice(qid, qtext, choices):
        if not choices:
            return "1"
            
        choice_items = []
        for k, v in choices.items():
            disp = v.get("Display", "") if isinstance(v, dict) else str(v)
            recode = v.get("RecodeValue", k) if isinstance(v, dict) else str(k)
            choice_items.append((str(k), disp, str(recode)))

        qtext_lower = qtext.lower()

        # 1. Problem / Complaint questions -> ALWAYS select NO
        if any(w in qtext_lower for w in ["problem", "issue", "complaint", "wrong with"]):
            for k, disp, recode in choice_items:
                if disp.lower() == "no" or recode == "2" or "no" in disp.lower():
                    return k
            return choice_items[-1][0]

        # 2. Team Member Recognition questions -> Select NO (to avoid long text follow-up) or YES if forced
        if "recognize a team member" in qtext_lower:
            for k, disp, recode in choice_items:
                if disp.lower() == "no" or recode == "2" or "no" in disp.lower():
                    return k

        # 3. Visit Confirmation -> YES
        if "visit on" in qtext_lower or "is your feedback related to" in qtext_lower:
            for k, disp, recode in choice_items:
                if disp.lower() == "yes" or recode == "1" or "yes" in disp.lower():
                    return k

        # 4. Loyalty / Rewards Scan questions -> YES
        if "tims rewards" in qtext_lower or "rewards card" in qtext_lower:
            for k, disp, recode in choice_items:
                if "yes" in disp.lower() or recode == "1":
                    return k

        # 5. Satisfaction / Likelihood rating questions -> HIGHLY SATISFIED / EXCELLENT / 5 / HIGHLY LIKELY
        satisfaction_keywords = ["satisfied", "satisfaction", "likelihood", "recommend", "rate", "overall", "quality", "cleanliness", "speed", "taste", "friendly"]
        if any(w in qtext_lower for w in satisfaction_keywords):
            # Find Highly Satisfied / Satisfied / 5 / top recode
            for k, disp, recode in choice_items:
                d_lower = disp.lower()
                if "highly satisfied" in d_lower or "extremely satisfied" in d_lower or "highly likely" in d_lower or "excellent" in d_lower:
                    return k
            for k, disp, recode in choice_items:
                if "satisfied" in disp.lower() or "likely" in disp.lower() or recode in ["5", "4", "1"]:
                    return k

        # 6. Order Type (Drive-thru / Dine-in / Takeout)
        if "order type" in qtext_lower or "how did you" in qtext_lower or "place your order" in qtext_lower:
            for k, disp, recode in choice_items:
                d_lower = disp.lower()
                if any(opt in d_lower for opt in ["drive-thru", "drive thru", "counter", "front counter", "dine in", "takeout"]):
                    return k

        # 7. Default to highest recode value or first option
        for k, disp, recode in choice_items:
            if recode in ["5", "1", "yes"]:
                return k
        return choice_items[0][0]

    @staticmethod
    def select_matrix_answer(answers):
        if not answers:
            return "1"
        for k, v in answers.items():
            disp = v.get("Display", "").lower() if isinstance(v, dict) else ""
            if "highly satisfied" in disp or "extremely satisfied" in disp or "excellent" in disp:
                return str(k)
        for k, v in answers.items():
            disp = v.get("Display", "").lower() if isinstance(v, dict) else ""
            if "satisfied" in disp or "agree" in disp:
                return str(k)
        return list(answers.keys())[0]


class TellTimsBot:
    def __init__(self, log_callback=None):
        self.base_url = "https://rbixm.qualtrics.com"
        self.survey_id = "SV_3lMYn8fpUtkEu7c"
        self.init_url = "https://rbixm.qualtrics.com/jfe/form/SV_3lMYn8fpUtkEu7c?CountryCode=CAN&InviteType=Coupon&SC=21"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session = requests.Session()
        self.log_callback = log_callback
        self.logs = []
        
        self.form_session_id = None
        self.xsrf_token = None
        self.brand_dc = "https://iad1.qualtrics.com"
        self.jfe_version = ""
        self.survey_version = ""
        self.runtime_payload = None

    def log(self, msg):
        self.logs.append(msg)
        if callable(self.log_callback):
            self.log_callback(msg)
        else:
            print(msg)

    def initialize_session(self):
        self.log("[*] Connecting to Qualtrics survey server...")
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        resp = self.session.get(self.init_url, headers=headers)
        if resp.status_code != 200:
            self.log(f"[-] Failed to load initial page (Status: {resp.status_code})")
            return False, None, None

        func_idx = resp.text.find("(function(appData)")
        if func_idx == -1:
            self.log("[-] Could not find appData function in HTML")
            return False, None, None

        call_idx = resp.text.find("})({", func_idx)
        if call_idx == -1:
            self.log("[-] Could not find appData JSON in HTML")
            return False, None, None

        json_start = call_idx + 3
        json_decoder = json.JSONDecoder()
        try:
            data, end = json_decoder.raw_decode(resp.text[json_start:])
        except Exception as e:
            self.log(f"[-] JSON decode error: {e}")
            return False, None, None

        sm = data.get("SM", {})
        self.form_session_id = sm.get("FormSessionID")
        self.xsrf_token = sm.get("XSRFToken")
        self.survey_id = sm.get("SurveyID", self.survey_id)
        self.brand_dc = sm.get("BrandDataCenterURL", self.brand_dc)
        self.jfe_version = sm.get("JFEVersionID", "")
        self.survey_version = sm.get("SurveyVersionID", "")
        self.runtime_payload = data.get("RuntimePayload")

        initial_qids = data.get("QuestionIDs", ["QID167", "QID9"])
        initial_defs = data.get("QuestionDefinitions", {})

        self.log(f"[+] Established Session ID: {self.form_session_id}")
        self.log(f"[+] Security Token: {self.xsrf_token[:10]}...")
        return True, initial_qids, initial_defs

    def solve(self, survey_code):
        survey_code = re.sub(r'[^0-9]', '', str(survey_code))
        if len(survey_code) < 10:
            return {"success": False, "validation_code": None, "message": "Invalid receipt survey code format."}

        ok, current_qids, current_defs = self.initialize_session()
        if not ok:
            return {"success": False, "validation_code": None, "message": "Could not connect to survey backend."}

        post_headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": self.init_url,
            "Xsrftoken": self.xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

        tid = 1
        step = 0
        max_steps = 35

        while step < max_steps:
            step += 1
            self.log(f"\n[Step {step}] Answering {len(current_qids)} questions dynamically...")

            questions_payload = {}
            for qid in current_qids:
                qdef = current_defs.get(qid, {})
                qtype = qdef.get("Type")
                qselector = qdef.get("Selector")
                raw_qtext = qdef.get("QuestionText", "")
                qtext = re.sub(r'<[^>]+>', ' ', raw_qtext).strip()

                q_obj = dict(qdef)
                q_obj["Valid"] = False
                q_obj["Active"] = True
                q_obj["Displayed"] = True

                # Receipt Code Input
                if qid == "QID9":
                    self.log(f"  📝 [QID9] Submitting Receipt Code: {survey_code}")
                    q_obj["Value"] = survey_code
                
                # Descriptive Information Screens
                elif qtype == "DB" or qselector == "TB":
                    self.log(f"  ℹ️  [{qid}] Info/Welcome Screen")
                
                # Free-form Text / Feedback Questions
                elif qtype == "TE" or qselector in ["SL", "ML"]:
                    val = SmartQuestionSolver.get_text_answer(qtext)
                    if val:
                        self.log(f"  💬 [{qid}] Auto-generated Comment: \"{val}\"")
                    else:
                        self.log(f"  ⏭️ [{qid}] Optional Text Input (Skipped)")
                    q_obj["Value"] = val
                    q_obj["Skipped"] = not bool(val)
                
                # Matrix / Likert Table Rating Questions
                elif qtype == "Matrix" or qselector in ["Likert", "Matrix"]:
                    choices = q_obj.get("Choices", {})
                    answers = q_obj.get("Answers", {})
                    best_ans = SmartQuestionSolver.select_matrix_answer(answers)
                    ans_label = answers.get(best_ans, {}).get("Display", "Top Rating") if isinstance(answers.get(best_ans), dict) else "Top Rating"
                    self.log(f"  ⭐ [{qid}] Matrix Rating ({len(choices)} items) => \"{ans_label}\"")
                    
                    for cid in choices:
                        if isinstance(choices[cid], dict):
                            choices[cid]["Selected"] = True
                    q_obj["Selected"] = None
                
                # Multi-Select Checkboxes (MAVR / MACOL)
                elif qselector in ["MAVR", "MACOL"] or qtype == "MC" and q_obj.get("ColumnCount"):
                    choices = q_obj.get("Choices", {})
                    choice_keys = list(choices.keys())
                    selected_keys = choice_keys[:2] if len(choice_keys) >= 2 else choice_keys[:1]
                    sel_names = [choices[k].get("Display", k) for k in selected_keys if isinstance(choices.get(k), dict)]
                    self.log(f"  ☑️ [{qid}] Multi-Select: {', '.join(sel_names)}")
                    for k in choices:
                        if isinstance(choices[k], dict):
                            choices[k]["Selected"] = (k in selected_keys)
                    q_obj["Selected"] = None
                
                # Single Choice Multiple Choice Questions (MC / SAVR / SAHR)
                else:
                    choices = q_obj.get("Choices", {})
                    selected_choice = SmartQuestionSolver.select_best_choice(qid, qtext, choices)
                    disp_text = choices.get(selected_choice, {}).get("Display", selected_choice) if isinstance(choices.get(selected_choice), dict) else selected_choice
                    
                    short_q = (qtext[:45] + "...") if len(qtext) > 45 else qtext
                    self.log(f"  🔘 [{qid}] {short_q} => \"{disp_text}\"")

                    for k in choices:
                        if isinstance(choices[k], dict):
                            choices[k]["Selected"] = (str(k) == str(selected_choice))
                    q_obj["Selected"] = str(selected_choice)

                questions_payload[qid] = q_obj

            body = {
                "SM": {
                    "Resolution": "1536x864", "FlashVersion": -1, "JavaSupport": 0, "IsIncognito": False,
                    "BaseServiceURL": self.base_url, "SurveyVersionID": self.survey_version,
                    "IsBrandEncrypted": False, "JFEVersionID": self.jfe_version,
                    "BrandDataCenterURL": self.brand_dc, "XSRFToken": self.xsrf_token,
                    "StartDate": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                    "StartDateRaw": int(time.time() * 1000), "BrandID": "rbixm",
                    "SurveyID": self.survey_id, "BrowserName": "Chrome", "BrowserVersion": "120.0.0.0",
                    "OS": "Windows NT 10.0", "UserAgent": self.user_agent, "LastUserAgent": self.user_agent,
                    "QueryString": "CountryCode=CAN&InviteType=Coupon&SC=21", "IP": "127.0.0.1",
                    "URL": self.init_url, "BaseHostURL": self.base_url, "ProxyURL": self.init_url,
                    "JFEDataCenter": "spoke9", "dataCenterPath": "jfe9", "IsPreview": False,
                    "LinkType": "anonymous", "EDFromRequest": ["CountryCode", "InviteType", "SC"],
                    "FormSessionID": self.form_session_id, "Q_RelevantIDFraudScore": 0,
                    "Q_RelevantIDDuplicate": False, "Q_RelevantIDDuplicateScore": 0
                },
                "ED": {
                    "SID": self.survey_id, "SurveyID": self.survey_id, "Q_URL": self.init_url,
                    "UserAgent": self.user_agent, "Q_CHL": "anonymous", "Q_Language": "EN",
                    "Q_RelevantIDFraudScore": 0, "Q_RelevantIDDuplicate": False,
                    "Q_RelevantIDDuplicateScore": 0
                },
                "EDMETA": {},
                "FormRuntime": None,
                "RuntimePayload": self.runtime_payload if step == 1 else None,
                "FormSessionID": self.form_session_id,
                "Questions": questions_payload,
                "TransactionID": tid,
                "OverridePDPWarning": False,
                "PageAnalytics": {},
                "ProgressState": []
            }

            rand = random.random()
            t = int(time.time() * 1000)
            post_url = f"{self.base_url}/jfe9/form/{self.survey_id}/next?rand={rand}&tid={tid}&t={t}&fs={self.form_session_id}"

            resp = self.session.post(post_url, headers=post_headers, json=body)
            if resp.status_code != 200:
                return {"success": False, "validation_code": None, "message": f"Server error {resp.status_code}: {resp.text[:200]}"}

            resp_data = resp.json()

            # Server error handling
            if resp_data.get("errorCode"):
                err = resp_data.get("errorCode")
                self.log(f"[-] Qualtrics Error: {err}")
                return {"success": False, "validation_code": None, "message": f"Server response: {err}"}

            # Check End of Survey
            messages = resp_data.get("Messages", {})
            if "EOSMessage" in messages:
                eos_text = messages["EOSMessage"].get("FinalEOSMessage", "")
                self.log("\n[🎉] Survey Flow Reached Final Completion!")

                code_match = re.search(r'Validation Code:\s*([A-Z0-9]+)', eos_text, re.IGNORECASE)
                if code_match:
                    val_code = code_match.group(1).strip()
                    self.log(f"[✨ SUCCESS] Validation Code: {val_code}")
                    return {
                        "success": True,
                        "validation_code": val_code,
                        "message": f"Survey completed successfully! Coupon Code: {val_code}"
                    }

                clean_text = re.sub(r'<[^>]+>', ' ', eos_text).strip()
                if "already been used" in clean_text.lower():
                    return {
                        "success": False,
                        "validation_code": None,
                        "message": "This receipt survey code has ALREADY BEEN USED."
                    }

                return {
                    "success": True,
                    "validation_code": None,
                    "message": clean_text
                }

            next_qids = resp_data.get("QuestionIDs", [])
            has_next_btn = bool(resp_data.get("NextButton"))

            if not next_qids and not has_next_btn:
                return {
                    "success": False,
                    "validation_code": None,
                    "message": "Survey ended early. The code might be expired or already redeemed."
                }

            current_qids = next_qids
            current_defs = resp_data.get("QuestionDefinitions", {})
            tid += 2
            time.sleep(0.35)

        return {"success": False, "validation_code": None, "message": "Survey step limit reached."}

def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("================================================================")
    print("  🍩 TELL TIMS SMART SURVEY AUTO-SOLVER (AI-POWERED)")
    print("================================================================")

    if len(sys.argv) > 1 and sys.argv[1].strip():
        survey_codes = [sys.argv[1].strip()]
        interactive = False
    else:
        interactive = True

    while True:
        if interactive:
            print("\n----------------------------------------------------------------")
            survey_code = input("👉 Enter Receipt Survey Code (or 'q' to quit): ").strip()
            if not survey_code or survey_code.lower() == 'q':
                print("[*] Exiting. Have a great day!")
                break
        else:
            survey_code = survey_codes.pop(0)

        cleaned_code = re.sub(r'[^0-9]', '', survey_code)
        if len(cleaned_code) < 10:
            print("[-] Invalid code! Please enter all digits from the receipt.")
            if not interactive:
                break
            continue

        print(f"\n[*] Solving survey for Receipt: {cleaned_code} ...")
        bot = TellTimsBot()
        res = bot.solve(cleaned_code)

        print("\n================================================================")
        if res["success"] and res.get("validation_code"):
            print("  🎉🎉🎉 SURVEY COMPLETED SUCCESSFULLY! 🎉🎉🎉")
            print("  --------------------------------------------------------------")
            print(f"  🎟️  VALIDATION COUPON CODE :  [ {res['validation_code']} ]")
            print("  --------------------------------------------------------------")
            print("  👉 Write this code on your receipt to redeem your offer!")
        elif res["success"]:
            print("  [+] Survey Response:")
            print(f"  {res['message']}")
        else:
            print("  [-] RESULT / ERROR:")
            print(f"  {res['message']}")
        print("================================================================")

        if not interactive:
            break

if __name__ == "__main__":
    main()
