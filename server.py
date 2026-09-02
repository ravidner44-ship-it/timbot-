#!/usr/bin/env python3
"""
Standalone Web Server for Tell Tims Survey Bot
Runs directly on Python: python server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import os
import sys

# Ensure execution directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "execution"))
from tims_bot import TellTimsBot

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tell Tims Survey Auto-Solver</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-2xl w-full bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-8">
        <div class="flex items-center space-x-4 mb-6 pb-6 border-b border-slate-700">
            <div class="w-14 h-14 bg-red-600/20 text-red-500 rounded-xl flex items-center justify-center text-2xl border border-red-500/30">
                <i class="fa-solid fa-mug-hot"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold text-white tracking-wide">Tell Tims Survey Bot</h1>
                <p class="text-sm text-slate-400">Automated Qualtrics Feedback & Validation Code Generator</p>
            </div>
        </div>

        <form method="POST" action="/" class="space-y-5">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">
                    <i class="fa-solid fa-receipt mr-1 text-red-400"></i> Receipt Survey Code (Numbers Only)
                </label>
                <input 
                    type="text" 
                    name="survey_code" 
                    required 
                    placeholder="e.g. 200291702132101060437"
                    value="{survey_code}"
                    class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all font-mono"
                >
            </div>

            <button 
                type="submit" 
                class="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg shadow-red-900/30 transition-all flex items-center justify-center space-x-2 cursor-pointer"
            >
                <i class="fa-solid fa-bolt"></i>
                <span>Generate Validation Coupon</span>
            </button>
        </form>

        {result_html}
    </div>
</body>
</html>
"""

class SurveyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = HTML_TEMPLATE.format(survey_code="", result_html="")
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        params = urllib.parse.parse_qs(post_data)
        survey_code = params.get("survey_code", [""])[0]

        logs = []
        def log_cb(msg):
            logs.append(msg)

        bot = TellTimsBot(log_callback=log_cb)
        result = bot.solve(survey_code)

        result_html = ""
        if result["success"] and result.get("validation_code"):
            result_html = f"""
            <div class="mt-8 space-y-4">
                <div class="bg-emerald-950/40 border border-emerald-500/30 rounded-2xl p-6 text-center">
                    <span class="text-xs uppercase tracking-widest font-semibold text-emerald-400 block mb-1">Coupon Validation Code</span>
                    <div class="text-4xl font-extrabold text-emerald-400 font-mono tracking-wider py-2">
                        {result['validation_code']}
                    </div>
                    <p class="text-sm text-slate-300 mt-2">Write this code on your receipt to redeem your offer!</p>
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4">
                    <div class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Execution Logs:</div>
                    <pre class="text-xs text-slate-300 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap">{chr(10).join(logs)}</pre>
                </div>
            </div>
            """
        elif result["success"]:
            result_html = f"""
            <div class="mt-8 space-y-4">
                <div class="bg-blue-950/40 border border-blue-500/30 rounded-xl p-5 text-blue-300">
                    <i class="fa-solid fa-check-circle mr-2"></i> {result['message']}
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4">
                    <div class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Execution Logs:</div>
                    <pre class="text-xs text-slate-300 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap">{chr(10).join(logs)}</pre>
                </div>
            </div>
            """
        else:
            result_html = f"""
            <div class="mt-8 space-y-4">
                <div class="bg-rose-950/40 border border-rose-500/30 rounded-xl p-5 text-rose-300">
                    <i class="fa-solid fa-triangle-exclamation mr-2"></i> {result['message']}
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4">
                    <div class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Execution Logs:</div>
                    <pre class="text-xs text-slate-300 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap">{chr(10).join(logs)}</pre>
                </div>
            </div>
            """

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = HTML_TEMPLATE.format(survey_code=survey_code, result_html=result_html)
        self.wfile.write(html.encode("utf-8"))

def run():
    server_address = ("127.0.0.1", 8088)
    httpd = HTTPServer(server_address, SurveyHandler)
    print("=======================================================")
    print(" 🚀 Tell Tims Survey Bot Live at: http://127.0.0.1:8088")
    print("=======================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
