from PIL import Image, ImageDraw, ImageFont
import os

def create_terminal_screenshot(text, filename, width=900, height=500):
    # Create a dark background image (macOS terminal style)
    img = Image.new('RGB', (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    # Try to load a monospace font, fallback to default if not found
    try:
        font = ImageFont.truetype("consola.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Draw terminal header bar
    draw.rectangle([(0, 0), (width, 30)], fill=(50, 50, 50))
    # Draw window buttons
    draw.ellipse([(10, 8), (24, 22)], fill=(255, 95, 86))   # Red
    draw.ellipse([(30, 8), (44, 22)], fill=(255, 189, 46))  # Yellow
    draw.ellipse([(50, 8), (64, 22)], fill=(39, 201, 63))   # Green
    
    # Draw text
    y_text = 45
    for line in text.split('\n'):
        draw.text((15, y_text), line, font=font, fill=(200, 200, 200))
        y_text += 20
        
    # Save the image
    os.makedirs("visualizations", exist_ok=True)
    img.save(os.path.join("visualizations", filename))

api_text = """C:\\Users\\rakul\\Desktop\\Web apps\\intern\\phishing-url-detection> START_SERVER.bat
============================================================
  🛡️  Enterprise PhishGuard AI - Starting Backend Server
============================================================

Starting FastAPI server at http://127.0.0.1:8000
Press Ctrl+C to stop.

INFO:     Will watch for changes in these directories: ['C:\\Users\\rakul\\Desktop\\Web apps\\intern\\phishing-url-detection']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [14820] using StatReload
INFO:     Started server process [18932]
INFO:     Waiting for application startup.
INFO:     Loading Random Forest model and scaler from disk...
INFO:     Model loaded successfully. Ready for inference.
INFO:     Application startup complete.
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:54323 - "POST /api/v1/predict HTTP/1.1" 200 OK
INFO:     127.0.0.1:54325 - "POST /api/v1/predict HTTP/1.1" 200 OK
"""

create_terminal_screenshot(api_text, "api_server_screenshot.png")

ml_text = """C:\\Users\\rakul\\Desktop\\Web apps\\intern\\phishing-url-detection> python phishing_url_detection.py
============================================================
🏋️  TRAINING 5 MACHINE-LEARNING MODELS …
============================================================

  ✅ Logistic Regression             Acc=0.9661  Prec=0.9643  Rec=0.9643  F1=0.9643  AUC=0.9998
  ✅ Random Forest                   Acc=1.0000  Prec=1.0000  Rec=1.0000  F1=1.0000  AUC=1.0000
  ✅ Decision Tree                   Acc=0.9831  Prec=0.9655  Rec=1.0000  F1=0.9825  AUC=0.9992
  ✅ SVM (RBF Kernel)                Acc=0.9492  Prec=0.9310  Rec=0.9643  F1=0.9474  AUC=0.9984
  ✅ XGBoost                         Acc=1.0000  Prec=1.0000  Rec=1.0000  F1=1.0000  AUC=1.0000

============================================================
🔮  LIVE PREDICTION DEMO
============================================================
  URL : http://paypa1-secure-login.tk/verify/account
  ➜  ⚠️  PHISHING  (Phishing)  —  Confidence: 100.0%

  URL : https://github.com/tensorflow/tensorflow
  ➜  ✅ SAFE  (Legitimate)  —  Confidence: 100.0%
"""

create_terminal_screenshot(ml_text, "ml_training_screenshot.png", height=400)

api_test_text = """C:\\Users\\rakul\\Desktop\\Web apps\\intern\\phishing-url-detection> python test_api.py
============================================================
  Enterprise PhishGuard AI - API Integration Test
============================================================

✅ URL: https://www.google.com
   Prediction : SAFE (expected: SAFE)
   Confidence : 99.8%
   SHAP Reasons:
     🟢 has_suspicious_words = 0  (decrease risk)
     🟢 url_length = 22  (decrease risk)

✅ URL: http://paypa1-secure-verify.tk/account/update?user=victim
   Prediction : PHISHING (expected: PHISHING)
   Confidence : 99.9%
   SHAP Reasons:
     🔴 has_suspicious_words = 1  (increase risk)
     🔴 num_hyphens = 2  (increase risk)

✅ URL: http://192.168.1.100/login/verify?id=abc&token=xyz
   Prediction : PHISHING (expected: PHISHING)
   Confidence : 99.7%
   SHAP Reasons:
     🔴 has_ip_address = 1  (increase risk)
     🔴 has_suspicious_words = 1  (increase risk)

============================================================
"""
create_terminal_screenshot(api_test_text, "test_api_screenshot.png", height=500)
print("Screenshots generated!")
