import os
import re
import math
import joblib
import numpy as np
from collections import Counter
from urllib.parse import urlparse, parse_qs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shap

app = FastAPI(title="Phishing Detection Enterprise API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "phishing_url_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "feature_scaler.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

explainer = shap.TreeExplainer(model)

_IP_PATTERN = re.compile(r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)")
_SUSPICIOUS_WORDS = ["login", "verify", "update", "confirm", "account", "secure", "bank", "signin", "password", "suspend", "alert", "billing", "payment", "unlock", "reactivate", "identity", "refund", "reward", "prize", "claim", "urgent", "free", "winner", "limited"]
_SHORTENER_DOMAINS = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "ow.ly", "goo.gl", "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at"}

_POPULAR_DOMAINS = ["google", "facebook", "amazon", "apple", "microsoft", "paypal", "netflix", "instagram", "linkedin"]

def _is_typosquatting(hostname: str) -> int:
    import difflib
    if not hostname: return 0
    parts = hostname.split('.')
    domain_part = parts[-2] if len(parts) > 1 else hostname
    for pop in _POPULAR_DOMAINS:
        if pop == domain_part:
            continue
        ratio = difflib.SequenceMatcher(None, pop, domain_part).ratio()
        if ratio >= 0.75:
            return 1
    return 0


def _brand_in_subdomain(hostname: str) -> int:
    parts = hostname.split('.')
    if len(parts) <= 2:
        return 0
    subdomains = parts[:-2]
    for brand in _POPULAR_DOMAINS:
        for sub in subdomains:
            if brand in sub:
                return 1
    return 0

def _shannon_entropy(s: str) -> float:
    if not s: return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())

def extract_features(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url_with_scheme = "http://" + url
    else:
        url_with_scheme = url

    parsed = urlparse(url_with_scheme)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    num_letters = sum(c.isalpha() for c in url)
    num_digits = sum(c.isdigit() for c in url)

    feats = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "tld_length": len(hostname.rsplit(".", 1)[-1]) if "." in hostname else 0,
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "num_slashes": url.count("/"),
        "num_question_marks": url.count("?"),
        "num_equals": url.count("="),
        "num_ampersands": url.count("&"),
        "num_at_signs": url.count("@"),
        "num_digits": num_digits,
        "num_special_chars": sum(not c.isalnum() and c not in (".", "/", ":", "?", "=", "&", "#") for c in url),
        "has_ip_address": int(bool(_IP_PATTERN.search(url))),
        "has_https": int(url_with_scheme.startswith("https://")),
        "has_http": int(url_with_scheme.startswith("http://") and not url_with_scheme.startswith("https://")),
        "num_subdomains": max(0, len(hostname.split(".")) - 2),
        "has_suspicious_words": int(any(word in url.lower() for word in _SUSPICIOUS_WORDS)),
        "is_shortened": int(hostname in _SHORTENER_DOMAINS),
        "url_entropy": round(_shannon_entropy(url), 4),
        "num_params": len(parse_qs(query)),
        "path_depth": len([seg for seg in path.split("/") if seg]),
        "digit_to_letter_ratio": round(num_digits / num_letters if num_letters else 0, 4),
        "has_port": int(parsed.port is not None and parsed.port not in (80, 443)),
        "domain_has_digits": int(any(c.isdigit() for c in hostname)),
        "is_typosquatting": _is_typosquatting(hostname),
        "brand_in_subdomain": _brand_in_subdomain(hostname),
    }
    return feats

class URLRequest(BaseModel):
    url: str

@app.post("/predict")
def predict(req: URLRequest):
    raw_features = extract_features(req.url)
    feature_names = list(raw_features.keys())
    feature_values = list(raw_features.values())
    
    X_new = np.array([feature_values])
    X_scaled = scaler.transform(X_new)
    
    prediction = int(model.predict(X_scaled)[0])
    probability = model.predict_proba(X_scaled)[0]
    confidence = round(float(probability[prediction]) * 100, 2)
    
    shap_vals_all = explainer.shap_values(X_scaled)
    if isinstance(shap_vals_all, list):
        shap_vals = shap_vals_all[1][0]
    elif len(shap_vals_all.shape) == 3:
        shap_vals = shap_vals_all[0, :, 1]
    else:
        shap_vals = shap_vals_all[0]
    
    explanations = []
    for i, name in enumerate(feature_names):
        contribution = float(shap_vals[i])
        if abs(contribution) > 0.1:
            explanations.append({
                "feature": name,
                "value": raw_features[name],
                "contribution": round(contribution, 3),
                "impact": "Increases Phishing Risk" if contribution > 0 else "Decreases Phishing Risk",
                "color": "red" if contribution > 0 else "green"
            })
            
    explanations = sorted(explanations, key=lambda x: abs(x["contribution"]), reverse=True)[:4]

    return {
        "url": req.url,
        "prediction": "PHISHING" if prediction == 1 else "SAFE",
        "confidence": confidence,
        "explainable_ai": explanations
    }

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "extension", "popup.html"))

@app.get("/popup.js")
def get_popup_js():
    return FileResponse(os.path.join(BASE_DIR, "extension", "popup.js"))
