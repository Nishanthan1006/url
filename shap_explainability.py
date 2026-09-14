"""
SHAP Explainable AI Visualization
==================================
Run this script to generate SHAP explanation plots for your project report.
Make sure the model is already trained (run phishing_url_detection.py first).

Usage:
    python shap_explainability.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import matplotlib
matplotlib.use('Agg')

import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import os, re, math
from collections import Counter
from urllib.parse import urlparse, parse_qs

# ── Load model & scaler ──────────────────────────────────────────────────────
print("=" * 60)
print("  🧠 SHAP Explainable AI Analysis - PhishGuard Enterprise")
print("=" * 60)

model  = joblib.load("phishing_url_model.pkl")
scaler = joblib.load("feature_scaler.pkl")

# ── Re-extract a balanced set of sample URLs for SHAP analysis ───────────────
_IP_PATTERN = re.compile(r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)")
_SUSPICIOUS = ["login","verify","update","confirm","account","secure","bank","signin","password","suspend","alert","billing","payment","unlock","reactivate","identity","refund","reward","prize","claim","urgent","free","winner","limited"]
_SHORTENED  = {"bit.ly","tinyurl.com","t.co","is.gd","ow.ly","goo.gl","buff.ly","rebrand.ly","cutt.ly","shorturl.at"}

def _entropy(s):
    if not s: return 0.0
    c = Counter(s); n = len(s)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

def extract_features(url):
    u = ("http://"+url) if not url.startswith(("http://","https://")) else url
    parsed = urlparse(u)
    h = parsed.hostname or ""; p = parsed.path or ""; q = parsed.query or ""
    nd = sum(c.isdigit() for c in url); nl = sum(c.isalpha() for c in url)
    return {
        "url_length": len(url), "hostname_length": len(h), "path_length": len(p),
        "tld_length": len(h.rsplit(".",1)[-1]) if "." in h else 0,
        "num_dots": url.count("."), "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"), "num_slashes": url.count("/"),
        "num_question_marks": url.count("?"), "num_equals": url.count("="),
        "num_ampersands": url.count("&"), "num_at_signs": url.count("@"),
        "num_digits": nd, "num_special_chars": sum(not c.isalnum() and c not in "./:?=&#" for c in url),
        "has_ip_address": int(bool(_IP_PATTERN.search(url))),
        "has_https": int(u.startswith("https://")),
        "has_http": int(u.startswith("http://") and not u.startswith("https://")),
        "num_subdomains": max(0, len(h.split("."))-2),
        "has_suspicious_words": int(any(w in url.lower() for w in _SUSPICIOUS)),
        "is_shortened": int(h in _SHORTENED),
        "url_entropy": round(_entropy(url), 4),
        "num_params": len(parse_qs(q)),
        "path_depth": len([s for s in p.split("/") if s]),
        "digit_to_letter_ratio": round(nd/nl if nl else 0, 4),
        "has_port": int(parsed.port is not None and parsed.port not in (80, 443)),
        "domain_has_digits": int(any(c.isdigit() for c in h)),
    }

SAMPLE_URLS = [
    ("https://www.google.com",                              0),
    ("https://github.com/login",                            0),
    ("https://stackoverflow.com/questions/ask",             0),
    ("https://amazon.com/dp/B08N5WRWNW",                    0),
    ("https://linkedin.com/in/profile",                     0),
    ("http://paypa1-secure-verify.tk/account/update",       1),
    ("http://192.168.1.100/login/verify?id=abc&token=xyz",  1),
    ("http://secure-banking-login.ml/auth/signin.php",      1),
    ("http://g00gle-account-reactivate.cf/verify",          1),
    ("http://bit.ly/3xFakeLink",                            1),
]

rows, labels = [], []
for url, label in SAMPLE_URLS:
    rows.append(extract_features(url))
    labels.append(label)

df = pd.DataFrame(rows)
FEATURE_COLS = list(df.columns)
X = scaler.transform(df.values)

# ── SHAP Analysis ─────────────────────────────────────────────────────────────
print("\n[1/3] Computing SHAP values...")
background = np.zeros((1, len(FEATURE_COLS)))
explainer  = shap.LinearExplainer(model, background)
shap_values = explainer.shap_values(X)

os.makedirs("visualizations", exist_ok=True)

# ── Plot 1: SHAP Summary Bar Plot ─────────────────────────────────────────────
print("[2/3] Generating SHAP Summary Bar Plot...")
shap_df = pd.DataFrame(np.abs(shap_values), columns=FEATURE_COLS)
mean_abs = shap_df.mean().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 7), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")
bars = ax.barh(mean_abs.index, mean_abs.values, color="#4ECDC4", edgecolor="#2ecc71", linewidth=0.5)
ax.set_xlabel("Mean |SHAP Value| (Average Impact on Model Output)", color="white", fontsize=11)
ax.set_title("Feature Importance via SHAP\n(Explainable AI Analysis)", color="white", fontsize=14, fontweight="bold")
ax.tick_params(colors="white"); ax.spines[:].set_color("#444")
ax.set_facecolor("#1e1e2f")
for spine in ax.spines.values(): spine.set_color("#444")
plt.tight_layout()
plt.savefig("visualizations/shap_summary_bar.png", dpi=150, bbox_inches="tight", facecolor="#1e1e2f")
plt.close()
print("   Saved: visualizations/shap_summary_bar.png")

# ── Plot 2: SHAP Waterfall for one phishing URL ────────────────────────────────
print("[3/3] Generating SHAP Decision Explanation for a Phishing URL...")
phishing_idx = 6  # "http://paypa1-secure-verify.tk..."
shap_vals_for_url = shap_values[phishing_idx]

# Sort by contribution magnitude
sorted_idx = np.argsort(np.abs(shap_vals_for_url))[::-1][:10]
top_features = [FEATURE_COLS[i] for i in sorted_idx]
top_shap     = [shap_vals_for_url[i] for i in sorted_idx]
colors       = ["#e74c3c" if v > 0 else "#2ecc71" for v in top_shap]

fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")
bars = ax.barh(top_features[::-1], top_shap[::-1], color=colors[::-1])
ax.axvline(0, color="white", linewidth=0.8, linestyle="--")
ax.set_xlabel("SHAP Value (Red = Pushes toward PHISHING, Green = Pushes toward SAFE)", color="white", fontsize=9)
ax.set_title("SHAP Explanation: Why was this URL flagged as PHISHING?\nURL: paypa1-secure-verify.tk/account/update", color="white", fontsize=12, fontweight="bold")
ax.tick_params(colors="white")
for spine in ax.spines.values(): spine.set_color("#444")
plt.tight_layout()
plt.savefig("visualizations/shap_waterfall_explanation.png", dpi=150, bbox_inches="tight", facecolor="#1e1e2f")
plt.close()
print("   Saved: visualizations/shap_waterfall_explanation.png")

print("\n" + "=" * 60)
print("  SHAP Analysis Complete! 2 new visualizations saved.")
print("  These plots show WHY the model makes its decisions.")
print("  Perfect for your project report (Section 5.4)!")
print("=" * 60)
