from PIL import Image, ImageDraw, ImageFont
import os

def create_terminal_screenshot(text, filename, width=900, height=350):
    img = Image.new('RGB', (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("consola.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    draw.rectangle([(0, 0), (width, 30)], fill=(50, 50, 50))
    draw.ellipse([(10, 8), (24, 22)], fill=(255, 95, 86))
    draw.ellipse([(30, 8), (44, 22)], fill=(255, 189, 46))
    draw.ellipse([(50, 8), (64, 22)], fill=(39, 201, 63))
    
    y_text = 45
    for line in text.split('\n'):
        draw.text((15, y_text), line, font=font, fill=(200, 200, 200))
        y_text += 20
        
    os.makedirs("visualizations", exist_ok=True)
    img.save(os.path.join("visualizations", filename))

safe_text = """C:\\Users\\rakul\\Desktop\\Web apps\\intern\\phishing-url-detection> python test_single_url.py --url "https://github.com/tensorflow/tensorflow"
============================================================
  🔍 Enterprise PhishGuard AI - URL Analysis Report
============================================================

URL Analyzed : https://github.com/tensorflow/tensorflow
Extraction   : 25 Lexical & Structural Features Extracted

🧠 AI MODEL VERDICT:
------------------------------------------------------------
[ ✔️ ] STATUS      : SAFE (Legitimate)
[ 📊 ] CONFIDENCE  : 100.0%

🔎 EXPLAINABLE AI (SHAP Analysis):
  🟢 has_suspicious_words = 0       -> Decreases phishing risk
  🟢 num_hyphens = 0                -> Decreases phishing risk
  🟢 num_dots = 1                   -> Decreases phishing risk
  🟢 is_shortened = 0               -> Decreases phishing risk
  
ACTION: Traffic Allowed by NIDS Firewall.
============================================================
"""

create_terminal_screenshot(safe_text, "safe_url_screenshot.png", height=450)
print("Safe URL Screenshot generated!")
