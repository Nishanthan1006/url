"""
Quick test script to verify the Enterprise API is working.
Run AFTER starting the server with START_SERVER.bat
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

API_URL = "http://127.0.0.1:8000/predict"

test_urls = [
    ("https://www.google.com", "SAFE"),
    ("https://github.com/login", "SAFE"),
    ("http://paypa1-secure-verify.tk/account/update?user=victim", "PHISHING"),
    ("http://192.168.1.100/login/verify?id=abc&token=xyz", "PHISHING"),
    ("https://amazon.com/dp/B08N5WRWNW", "SAFE"),
]

print("=" * 60)
print("  Enterprise PhishGuard AI - API Integration Test")
print("=" * 60)

for url, expected in test_urls:
    try:
        resp = requests.post(API_URL, json={"url": url}, timeout=10)
        data = resp.json()
        match = "✅" if data["prediction"] == expected else "❌"
        print(f"\n{match} URL: {url[:60]}")
        print(f"   Prediction : {data['prediction']} (expected: {expected})")
        print(f"   Confidence : {data['confidence']}%")
        if data.get("explainable_ai"):
            print("   SHAP Reasons:")
            for e in data["explainable_ai"][:2]:
                icon = "🔴" if e["color"] == "red" else "🟢"
                print(f"     {icon} {e['feature']} = {e['value']}  ({e['impact']})")
    except Exception as ex:
        print(f"\n⚠️  Could not reach API: {ex}")
        print("   Make sure START_SERVER.bat is running first!")

print("\n" + "=" * 60)
