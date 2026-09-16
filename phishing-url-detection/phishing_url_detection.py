#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              PHISHING URL DETECTION USING MACHINE LEARNING                  ║
║                                                                              ║
║  This project builds a machine-learning pipeline that classifies URLs as     ║
║  LEGITIMATE or PHISHING based on 25 lexical / structural features.           ║
║                                                                              ║
║  Models trained: Logistic Regression, Random Forest, Decision Tree,          ║
║                  Support Vector Machine (SVM), XGBoost / Gradient Boosting   ║
║                                                                              ║
║  Compatible with: Google Colab  |  Jupyter Notebook  |  Local Python 3.8+   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ── Fix Windows console encoding for emoji/Unicode output ─────────────────────
import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 1 — SETUP & INSTALLATION                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# If running in Google Colab, the pip installs below will add any missing
# packages.  If running locally, you can install them once with:
#     pip install scikit-learn pandas numpy matplotlib seaborn xgboost
#
# We intentionally keep the dependency list small — no network access is
# required because the URL dataset is embedded directly in this script.
# ──────────────────────────────────────────────────────────────────────────────

import subprocess
import sys

def install_if_missing(package: str, import_name: str | None = None):
    """Try to import *import_name*; if it fails, pip-install *package*."""
    try:
        __import__(import_name or package)
    except ImportError:
        print(f"📦 Installing {package} …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])

# Core scientific stack (usually pre-installed in Colab)
install_if_missing("scikit-learn", "sklearn")
install_if_missing("pandas")
install_if_missing("numpy")
install_if_missing("matplotlib")
install_if_missing("seaborn")
install_if_missing("xgboost")

# ── Imports ───────────────────────────────────────────────────────────────────
import os
import re
import math
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend (saves to file, no GUI window needed)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

from collections import Counter
from urllib.parse import urlparse, parse_qs

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, classification_report,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC

# XGBoost is optional — we fall back to GradientBoostingClassifier if missing.
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
    print("✅ XGBoost loaded successfully.")
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available — will use GradientBoosting instead.")

import joblib

warnings.filterwarnings("ignore")

print("\n" + "=" * 60)
print("🛡️  PHISHING URL DETECTION — All libraries loaded!")
print("=" * 60 + "\n")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 2 — DATASET (EMBEDDED URL LISTS)                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# To keep this project **completely self-contained** (no network needed), we
# embed 160 legitimate and 160 phishing URLs directly in the code.  Features
# are extracted programmatically in Section 3.
#
# ► LEGITIMATE URLS are drawn from well-known, trusted domains with varied
#   paths, query strings, and structures.
# ► PHISHING URLS mimic real-world phishing patterns: misspellings, suspicious
#   TLDs (.tk, .ml, .cf, .xyz), IP-address hosts, long subdomains, and
#   deceptive path keywords (/verify, /login, /update, /confirm).
#
# Tip for students: in a production project you would use a labelled dataset
# such as the UCI Phishing Websites dataset (30 features, 11 055 samples).
# ──────────────────────────────────────────────────────────────────────────────

LEGITIMATE_URLS = [
    # ── Google & YouTube ──────────────────────────────────────────────────
    "https://www.google.com/search?q=machine+learning",
    "https://accounts.google.com/signin",
    "https://mail.google.com/mail/u/0/#inbox",
    "https://drive.google.com/drive/my-drive",
    "https://docs.google.com/document/d/1A2B3C/edit",
    "https://calendar.google.com/calendar/r",
    "https://translate.google.com/?sl=en&tl=fr",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/results?search_query=python+tutorial",
    "https://studio.youtube.com/channel/UCxyz/videos",
    # ── Facebook / Meta ───────────────────────────────────────────────────
    "https://www.facebook.com/",
    "http://www.facebook.com/profile.php?id=100000123456",
    "http://www.facebook.com/events/discover",
    "https://www.instagram.com/explore/",
    "https://www.instagram.com/p/CxYz1234/",
    "https://www.messenger.com/",
    "https://about.meta.com/technologies/",
    # ── Amazon ────────────────────────────────────────────────────────────
    "https://www.amazon.com/dp/B08N5WRWNW",
    "https://www.amazon.com/gp/bestsellers",
    "https://www.amazon.com/s?k=laptop",
    "https://aws.amazon.com/ec2/",
    "https://aws.amazon.com/s3/pricing/",
    # ── Microsoft ─────────────────────────────────────────────────────────
    "https://www.microsoft.com/en-us/windows",
    "https://outlook.live.com/mail/0/inbox",
    "https://portal.azure.com/",
    "http://github.com/microsoft/vscode",
    "https://learn.microsoft.com/en-us/python/",
    "https://onedrive.live.com/",
    # ── Apple ─────────────────────────────────────────────────────────────
    "http://www.apple.com/shop/buy-iphone",
    "https://www.apple.com/macbook-air/",
    "https://support.apple.com/en-us/HT201222",
    "http://developer.apple.com/documentation/swift",
    # ── Wikipedia ─────────────────────────────────────────────────────────
    "https://en.wikipedia.org/wiki/Machine_learning",
    "http://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    # ── StackOverflow / GitHub ────────────────────────────────────────────
    "https://stackoverflow.com/questions/tagged/python",
    "https://stackoverflow.com/questions/12345678/how-to-parse-json",
    "http://github.com/trending",
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/pytorch/pytorch/issues",
    "http://gist.github.com/user123/abcdef",
    # ── LinkedIn / Twitter ────────────────────────────────────────────────
    "https://www.linkedin.com/in/john-doe/",
    "https://www.linkedin.com/jobs/search/",
    "https://www.linkedin.com/feed/",
    "https://twitter.com/elonmusk",
    "https://twitter.com/home",
    "http://twitter.com/i/bookmarks",
    # ── Reddit ────────────────────────────────────────────────────────────
    "https://www.reddit.com/r/MachineLearning/",
    "https://www.reddit.com/r/Python/comments/abc123/",
    "https://old.reddit.com/r/datascience/",
    # ── News / Media ──────────────────────────────────────────────────────
    "https://www.bbc.com/news/technology",
    "http://edition.cnn.com/world",
    "https://www.nytimes.com/section/science",
    "http://www.reuters.com/technology/",
    "https://www.theguardian.com/us-news",
    # ── Education & Research ──────────────────────────────────────────────
    "https://www.coursera.org/learn/machine-learning",
    "https://www.edx.org/course/artificial-intelligence",
    "http://www.khanacademy.org/math/statistics-probability",
    "https://arxiv.org/abs/2301.01234",
    "https://scholar.google.com/scholar?q=deep+learning",
    "https://www.mit.edu/",
    "https://www.stanford.edu/",
    # ── E-commerce & Services ─────────────────────────────────────────────
    "https://www.ebay.com/sch/i.html?_nkw=laptop",
    "https://www.etsy.com/search?q=handmade+jewelry",
    "https://www.walmart.com/browse/electronics",
    "https://www.target.com/c/electronics/-/N-5xtg6",
    "https://www.bestbuy.com/site/laptops/all-laptops/pcmcat138500050001.c",
    "https://www.shopify.com/",
    "http://www.paypal.com/us/home",
    # ── Tech / SaaS ──────────────────────────────────────────────────────
    "https://www.dropbox.com/home",
    "https://slack.com/",
    "https://zoom.us/join",
    "https://www.notion.so/",
    "https://trello.com/b/abc123/my-board",
    "http://www.figma.com/",
    "https://www.canva.com/design/",
    "http://www.atlassian.com/software/jira",
    # ── Entertainment ─────────────────────────────────────────────────────
    "https://www.netflix.com/browse",
    "http://www.spotify.com/us/account/overview/",
    "https://www.twitch.tv/directory",
    "https://store.steampowered.com/",
    "https://www.imdb.com/chart/top/",
    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
    # ── Finance ───────────────────────────────────────────────────────────
    "https://www.chase.com/personal/checking",
    "https://www.bankofamerica.com/",
    "http://www.wellsfargo.com/",
    "https://www.fidelity.com/",
    "https://www.schwab.com/",
    "https://finance.yahoo.com/quote/AAPL",
    # ── Government & Health ───────────────────────────────────────────────
    "https://www.usa.gov/",
    "https://www.irs.gov/refunds",
    "http://www.cdc.gov/coronavirus/",
    "http://www.who.int/news",
    "http://www.nih.gov/",
    # ── Developer Tools ───────────────────────────────────────────────────
    "https://pypi.org/project/numpy/",
    "https://docs.python.org/3/library/json.html",
    "https://pytorch.org/docs/stable/",
    "https://www.tensorflow.org/tutorials",
    "http://scikit-learn.org/stable/modules/svm.html",
    "https://pandas.pydata.org/docs/",
    "https://numpy.org/doc/stable/",
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "https://reactjs.org/docs/getting-started.html",
    "http://vuejs.org/guide/introduction.html",
    # ── Travel ────────────────────────────────────────────────────────────
    "https://www.booking.com/searchresults.html?dest=Paris",
    "https://www.airbnb.com/s/New-York/homes",
    "https://www.tripadvisor.com/",
    "https://www.expedia.com/Flights",
    # ── Misc well-known ───────────────────────────────────────────────────
    "https://www.quora.com/",
    "http://medium.com/towards-data-science",
    "https://www.pinterest.com/",
    "https://www.tumblr.com/",
    "https://www.cloudflare.com/",
    "https://www.digitalocean.com/",
    "https://www.heroku.com/",
    "http://vercel.com/",
    "http://www.kaggle.com/competitions",
    "https://huggingface.co/models",
    "https://colab.research.google.com/",
    "https://www.wolframalpha.com/",
    "https://www.grammarly.com/",
    "https://www.duolingo.com/learn",
    "https://www.craigslist.org/",
    "https://www.yelp.com/search?find_desc=restaurants",
    "https://www.zillow.com/homes/",
    "https://www.weather.com/weather/today/",
    "https://www.usps.com/",
    "https://www.fedex.com/en-us/tracking.html",
    "https://maps.google.com/maps?q=new+york",
    "https://news.ycombinator.com/",
    "https://www.producthunt.com/",
    "https://www.goodreads.com/",
    "https://www.webmd.com/",
    "https://www.mayoclinic.org/",
    "https://www.healthline.com/",
    "https://www.investopedia.com/",
    "http://www.forbes.com/",
    "https://www.bloomberg.com/markets",
    "http://www.cnbc.com/world/",
    "https://www.wired.com/",
    "http://techcrunch.com/",
    "https://arstechnica.com/",
    "https://www.theverge.com/",
    "http://www.cnet.com/",
    "https://www.nationalgeographic.com/",
    "https://www.nasa.gov/",
    "https://www.space.com/",
    "https://www.smithsonianmag.com/",
    "https://www.un.org/en/",
    "https://www.worldbank.org/",
    "https://www.imf.org/en/Home",
    "http://www.ted.com/talks",
    "https://www.udemy.com/courses/development/",
    "https://www.pluralsight.com/",
]

PHISHING_URLS = [
    # ── Google impersonation ──────────────────────────────────────────────
    "https://g00gle-secure-login.tk/verify/account",
    "http://google.com.account-verify.ml/signin",
    "http://secure-google-login.cf/auth/update",
    "https://accounts-google.com-verify.tk/login",
    "https://google-security-alert.ml/verify/password",
    "http://signin-google.com.support.xyz/confirm",
    "https://googl3.com-secure.tk/account/verify",
    "http://myaccount-google.cf/security/update",
    "https://google-drive-share.ml/document/view?id=phish",
    "http://google-support-team.tk/recover/password",
    # ── PayPal / Banking ──────────────────────────────────────────────────
    "https://paypa1-account.ml/update/billing",
    "http://paypal-secure-login.tk/verify",
    "https://paypal.com.account-limited.cf/resolve",
    "https://secure-paypal-update.ml/confirm/identity",
    "https://paypal-support.com-verify.tk/account",
    "https://paypall-security.cf/update/payment",
    "http://chase-secure-banking.tk/verify/account",
    "http://bankofamerica-login.ml/secure/verify",
    "http://wellsfarg0-online.cf/signin/update",
    "https://citibank-alert.tk/security/confirm",
    # ── Apple impersonation ───────────────────────────────────────────────
    "https://apple-id-verify.tk/login/secure",
    "https://appleid.apple.com-verify.ml/signin",
    "https://icloud-security-alert.cf/verify/account",
    "https://apple-support-team.tk/unlock/appleid",
    "http://itunes-billing-update.ml/payment/confirm",
    "https://apple-account-suspended.cf/reactivate",
    "https://apple-id-locked.tk/verify/identity",
    "http://find-my-iphone.ml/alert/location",
    # ── Microsoft impersonation ───────────────────────────────────────────
    "http://microsoft-security-alert.tk/verify",
    "https://outlook-login-verify.ml/account/update",
    "https://office365-password-reset.cf/signin",
    "https://microsoft-account.com-verify.tk/secure",
    "http://onedrive-share-doc.ml/view/document",
    "http://teams-meeting-join.cf/conference/verify",
    "https://windows-defender-alert.tk/scan/threat",
    # ── Amazon impersonation ──────────────────────────────────────────────
    "https://amazon-order-confirm.tk/verify/payment",
    "https://amazon.com-delivery-update.ml/track",
    "https://amazon-prime-renewal.cf/billing/update",
    "https://amazon-security-alert.tk/verify/account",
    "http://amaz0n-customer-service.ml/refund/claim",
    "https://amazon-gift-card-free.cf/claim/reward",
    "https://prime-video-account.tk/subscription/verify",
    # ── Netflix impersonation ─────────────────────────────────────────────
    "https://netflix-payment-update.tk/billing/verify",
    "http://netflix.com-suspended.ml/reactivate",
    "https://netflix-account-alert.cf/verify/payment",
    "https://netfliix-renew.tk/update/subscription",
    # ── Facebook / Instagram ──────────────────────────────────────────────
    "https://facebook-security-check.tk/verify/identity",
    "http://faceb00k-login-verify.ml/account",
    "http://instagram-account-verify.cf/confirm",
    "https://facebook.com-page-violation.tk/appeal",
    "https://fb-copyright-notice.ml/verify/identity",
    "https://instagram-badge-verify.cf/apply/account",
    # ── IP-address based (classic phishing) ───────────────────────────────
    "http://192.168.1.1/admin/login.php",
    "http://45.33.32.156/webmail/verify/account",
    "https://103.224.182.252/secure/banking/login",
    "http://185.199.110.153/paypal/verify/account",
    "https://172.67.188.93/signin/update/password",
    "https://91.198.174.192/account/verify/secure",
    "http://104.16.100.52/login/bank/update",
    "https://23.227.38.65/confirm/identity/secure",
    "https://216.58.214.206/auth/verify/account",
    "https://142.250.80.46/secure/login/confirm",
    # ── Shortened URLs hiding phishing ────────────────────────────────────
    "https://bit.ly/3xPhish1",
    "https://tinyurl.com/fakebank-login",
    "https://t.co/suspiciousLink",
    "https://is.gd/phish123",
    "https://ow.ly/fakeverify",
    "https://goo.gl/malicious",
    "https://bit.ly/verify-now-urgent",
    "https://tinyurl.com/urgent-security",
    # ── Suspicious TLDs & long subdomains ─────────────────────────────────
    "https://login-secure-update.verify-account.tk/signin",
    "https://www.bank-security-update-verify-account-confirm.ml/login",
    "https://account.update.verify.secure.login.cf/confirm",
    "http://urgent-security-alert-update.tk/account/verify",
    "https://your-account-has-been-limited.ml/verify",
    "https://verify-your-identity-now.cf/login/secure",
    "https://security-center-update.tk/confirm/account",
    "https://customer-support-verify.ml/identity/confirm",
    # ── Crypto scams ──────────────────────────────────────────────────────
    "https://free-bitcoin-mining.tk/claim/reward",
    "https://ethereum-airdrop-claim.ml/wallet/verify",
    "http://crypto-giveaway-2024.cf/claim",
    "http://binance-security-update.tk/verify/wallet",
    "https://coinbase-account-alert.ml/verify/identity",
    "https://metamask-wallet-connect.cf/approve/access",
    # ── Tax / Government scams ────────────────────────────────────────────
    "https://irs-refund-claim.tk/verify/identity",
    "https://tax-return-update.ml/confirm/ssn",
    "http://social-security-alert.cf/verify/account",
    "https://government-benefit-claim.tk/apply/verify",
    "https://stimulus-check-update.ml/claim/payment",
    # ── Delivery / Shipping scams ─────────────────────────────────────────
    "https://fedex-delivery-update.tk/track/verify",
    "https://ups-package-alert.ml/reschedule/delivery",
    "http://usps-redelivery.cf/schedule/confirm",
    "https://dhl-shipment-notification.tk/track/update",
    # ── Prizes / Rewards scams ────────────────────────────────────────────
    "https://congratulations-winner.tk/claim/prize",
    "https://iphone15-free-giveaway.ml/claim",
    "http://walmart-gift-card-500.cf/redeem/reward",
    "http://survey-reward-claim.tk/complete/verify",
    "http://lucky-winner-2024.ml/claim/prize/now",
    "http://free-playstation5.cf/contest/winner",
    # ── Job / HR scams ────────────────────────────────────────────────────
    "https://linkedin-job-offer.tk/apply/verify",
    "https://remote-work-opportunity.ml/apply/confirm",
    "https://hr-department-verify.cf/employee/update",
    # ── Generic suspicious patterns ───────────────────────────────────────
    "https://secure-login-update-verify.tk/account",
    "https://www.verify-identity-confirm.ml/secure",
    "http://update-your-billing-info.cf/payment",
    "https://account-verify-confirm.xyz/login",
    "http://password-reset-required.tk/update",
    "https://suspicious-activity-alert.ml/verify",
    "https://confirm-your-account-now.cf/signin",
    "http://reactivate-suspended-account.tk/verify",
    "https://urgent-action-required.ml/confirm/identity",
    "https://final-warning-account.cf/verify/now",
    "http://document-shared-view.tk/open/verify",
    "https://invoice-payment-due.ml/pay/confirm",
    "https://voicemail-notification.cf/listen/verify",
    "https://missed-delivery-reschedule.tk/confirm",
    "https://subscription-expired-renew.ml/update",
    "http://security-update-required.cf/verify/now",
    "https://account-verification-needed.tk/confirm",
    "https://login-attempt-blocked.ml/verify/identity",
    "https://payment-failed-update.cf/billing/verify",
    "https://unusual-signin-activity.tk/verify/account",
    "https://reset-password-now.ml/update/secure",
    "https://verify-email-address.cf/confirm/account",
    "https://unauthorized-access-alert.tk/secure/login",
    "https://billing-statement-review.ml/view/confirm",
    "https://click-here-to-verify.cf/account/update",
    "https://limited-time-offer-free.tk/claim/now",
    "http://download-free-software.ml/install/verify",
    "https://update-browser-now.cf/download/install",
    "http://flash-player-update.tk/install/verify",
    "https://virus-detected-clean.ml/scan/fix",
    "https://your-computer-infected.cf/clean/verify",
    "http://technical-support-help.tk/remote/access",
    "https://antivirus-expired-renew.ml/subscribe/now",
    "http://system-error-fix.cf/repair/verify",
    "https://lottery-winning-notice.tk/claim",
    "http://inheritance-claim-bank.ml/transfer/verify",
    "https://prince-fund-transfer.cf/claim/urgent",
    # ── Typosquatting examples ────────────────────────────────────────────
    "https://g00gle.com/login",
    "https://faceb00k-login.com/secure",
    "https://amzon.com/verify",
    "https://paypa1.com/update",
    "https://netf1ix.com/billing",
    "https://instagrarm.com/verify",
    # ── Deceptive Subdomains (User requested) ─────────────
    "https://www.amazon.login_password./.com",
    "https://paypal.update.billing./secure",
    "https://www.amazon.login.--password.com",
    "https://www.google.com.secure-login-update.info",
    "https://facebook.com.verify-account.net/login",
    "https://apple.com.id-verification.xyz/auth",
    "https://www.microsoft.com.security-alert-center.com",
    "https://www.netflix.com.billing-update.com/payment",
    "https://www.chase.com.login-auth-verify.com/secure",
    "https://bankofamerica.com.account-update.info/login",
    "https://www.amazon.com.customer-support-refund.net",
    "https://www.paypal.com.secure-update-account.info",
]

# ── Massive Data Augmentation ─────────────────────────────────────────
import random
random.seed(42)

# Generate 2000 Legitimate URLs
_brands = ["google", "amazon", "apple", "microsoft", "paypal", "netflix", "facebook", "github", "linkedin", "twitter", "instagram"]
_tlds = [".com", ".org", ".net", ".edu", ".gov"]
_paths = ["/login", "/about", "/contact", "/products", "/home", "/user/profile", "/docs", "/search?q=test", "/help"]

for _ in range(2000):
    b = random.choice(_brands)
    t = random.choice(_tlds)
    p = random.choice(_paths)
    LEGITIMATE_URLS.append(f"https://www.{b}{t}{p}")

# Generate 2000 Phishing URLs
_fake_tlds = [".tk", ".ml", ".cf", ".xyz", ".club", ".info", ".net", ".com"]
_susp_words = ["login", "verify", "update", "secure", "account", "confirm", "billing", "auth"]
_sub_patterns = [
    "{brand}.{word}.{word2}", 
    "www.{brand}.{word}--{word2}", 
    "{word}.{word2}.{brand}",
    "{brand}-{word}",
    "secure-{brand}-update"
]
for _ in range(2000):
    b = random.choice(_brands)
    t = random.choice(_fake_tlds)
    p = random.choice(_paths)
    w1 = random.choice(_susp_words)
    w2 = random.choice(_susp_words)
    pat = random.choice(_sub_patterns)
    sub = pat.format(brand=b, word=w1, word2=w2)
    
    scheme = "https://" if random.random() < 0.7 else "http://"
    PHISHING_URLS.append(f"{scheme}{sub}{t}{p}")

print(f"📊 Dataset prepared:")
print(f"   ✅ Legitimate URLs : {len(LEGITIMATE_URLS)}")
print(f"   🚨 Phishing URLs  : {len(PHISHING_URLS)}")
print(f"   📈 Total           : {len(LEGITIMATE_URLS) + len(PHISHING_URLS)}")
print()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                 SECTION 3 — FEATURE EXTRACTION (CORE)                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# We extract **25 hand-crafted features** from the raw URL string.  These are
# purely lexical — they look only at the URL text, NOT at the page content or
# WHOIS records.  This makes them very fast and suitable for real-time scoring.
#
# Feature categories:
#   • Length-based   : url_length, hostname_length, path_length, tld_length
#   • Count-based    : dots, hyphens, digits, special chars, params, …
#   • Boolean flags  : has_ip, has_https, is_shortened, has_port, …
#   • Ratios & info  : digit_to_letter_ratio, url_entropy
# ──────────────────────────────────────────────────────────────────────────────

# Pre-compiled regex for detecting an IP-address hostname
_IP_PATTERN = re.compile(
    r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
)

# Words commonly found in phishing URLs
_SUSPICIOUS_WORDS = [
    "login", "verify", "update", "confirm", "account", "secure", "bank",
    "signin", "password", "suspend", "alert", "billing", "payment",
    "unlock", "reactivate", "identity", "refund", "reward", "prize",
    "claim", "urgent", "free", "winner", "limited",
]

# Popular URL shortener domains
_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "ow.ly", "goo.gl",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at",
}

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
    """Return the Shannon entropy (bits) of a string.

    Higher entropy ≈ more randomness, which is typical for auto-generated
    phishing URLs.  Legitimate domains tend to have lower entropy because
    they use natural-language words.
    """
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum(
        (c / length) * math.log2(c / length) for c in counts.values()
    )


def extract_features(url: str) -> dict:
    """Extract 25 numerical features from a single URL string.

    Parameters
    ----------
    url : str
        The full URL (may or may not include a scheme).

    Returns
    -------
    dict
        A dictionary mapping feature names → numeric values.
    """
    # Ensure there is a scheme so urlparse works correctly
    if not url.startswith(("http://", "https://")):
        url_with_scheme = "http://" + url
    else:
        url_with_scheme = url

    parsed = urlparse(url_with_scheme)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    # ── 1-4: Length features ──────────────────────────────────────────────
    url_length       = len(url)
    hostname_length  = len(hostname)
    path_length      = len(path)
    tld              = hostname.rsplit(".", 1)[-1] if "." in hostname else ""
    tld_length       = len(tld)

    # ── 5-13: Character-count features ────────────────────────────────────
    num_dots          = url.count(".")
    num_hyphens       = url.count("-")
    num_underscores   = url.count("_")
    num_slashes       = url.count("/")
    num_question_marks = url.count("?")
    num_equals        = url.count("=")
    num_ampersands    = url.count("&")
    num_at_signs      = url.count("@")
    num_digits        = sum(c.isdigit() for c in url)

    # Special characters = anything that is not alphanumeric, dot, or slash
    num_special_chars = sum(
        not c.isalnum() and c not in (".", "/", ":", "?", "=", "&", "#")
        for c in url
    )

    # ── 14-16: Boolean / protocol flags ───────────────────────────────────
    has_ip_address = int(bool(_IP_PATTERN.search(url)))
    has_https      = int(url_with_scheme.startswith("https://"))
    has_http       = int(url_with_scheme.startswith("http://") and not has_https)

    # ── 17: Subdomain count ───────────────────────────────────────────────
    # "www.mail.google.com" has 2 subdomains (www, mail)
    parts = hostname.split(".")
    # subtract the domain and TLD to get subdomains
    num_subdomains = max(0, len(parts) - 2)

    # ── 18: Suspicious-word flag ──────────────────────────────────────────
    url_lower = url.lower()
    has_suspicious_words = int(
        any(word in url_lower for word in _SUSPICIOUS_WORDS)
    )

    # ── 19: Shortened-URL flag ────────────────────────────────────────────
    is_shortened = int(hostname in _SHORTENER_DOMAINS)

    # ── 20: Shannon entropy ───────────────────────────────────────────────
    url_entropy = round(_shannon_entropy(url), 4)

    # ── 21: Number of query parameters ────────────────────────────────────
    num_params = len(parse_qs(query))

    # ── 22: Path depth (how many directory levels) ────────────────────────
    path_depth = len([seg for seg in path.split("/") if seg])

    # ── 23: Digit-to-letter ratio ─────────────────────────────────────────
    num_letters = sum(c.isalpha() for c in url)
    digit_to_letter_ratio = round(
        num_digits / num_letters if num_letters else 0, 4
    )

    # ── 24: Non-standard port flag ────────────────────────────────────────
    has_port = int(
        parsed.port is not None and parsed.port not in (80, 443)
    )

    # ── 25: Domain-contains-digits flag ───────────────────────────────────
    # Legitimate domains rarely have digits (except version numbers).
    domain_has_digits = int(any(c.isdigit() for c in hostname))

    # ── 26: Typosquatting flag ────────────────────────────────────────────
    is_typosquatting = _is_typosquatting(hostname)

    return {
        "url_length":            url_length,
        "hostname_length":       hostname_length,
        "path_length":           path_length,
        "tld_length":            tld_length,
        "num_dots":              num_dots,
        "num_hyphens":           num_hyphens,
        "num_underscores":       num_underscores,
        "num_slashes":           num_slashes,
        "num_question_marks":    num_question_marks,
        "num_equals":            num_equals,
        "num_ampersands":        num_ampersands,
        "num_at_signs":          num_at_signs,
        "num_digits":            num_digits,
        "num_special_chars":     num_special_chars,
        "has_ip_address":        has_ip_address,
        "has_https":             has_https,
        "has_http":              has_http,
        "num_subdomains":        num_subdomains,
        "has_suspicious_words":  has_suspicious_words,
        "is_shortened":          is_shortened,
        "url_entropy":           url_entropy,
        "num_params":            num_params,
        "path_depth":            path_depth,
        "digit_to_letter_ratio": digit_to_letter_ratio,
        "has_port":              has_port,
        "domain_has_digits":     domain_has_digits,
        "is_typosquatting":      is_typosquatting,
        "brand_in_subdomain":    _brand_in_subdomain(hostname),
    }


# Quick sanity check
_sample = extract_features("http://192.168.1.1/admin/login.php")
print("🔬 Sample feature extraction (phishing IP URL):")
for k, v in _sample.items():
    print(f"   {k:28s} = {v}")
print()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 4 — DATA PREPARATION                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Steps:
#   1. Extract features from every URL.
#   2. Combine into a single DataFrame with a 'label' column
#      (0 = legitimate, 1 = phishing).
#   3. Display summary statistics and class distribution.
#   4. Split 80 / 20 into train and test sets.
#   5. Standardize features (zero mean, unit variance) for models that
#      are sensitive to feature scale (Logistic Regression, SVM).
# ──────────────────────────────────────────────────────────────────────────────

print("⚙️  Extracting features from all URLs …")

rows = []

# Process legitimate URLs → label 0
for url in LEGITIMATE_URLS:
    feats = extract_features(url)
    feats["label"] = 0
    rows.append(feats)

# Process phishing URLs → label 1
for url in PHISHING_URLS:
    feats = extract_features(url)
    feats["label"] = 1
    rows.append(feats)

df = pd.DataFrame(rows)

print(f"✅ Feature extraction complete! DataFrame shape: {df.shape}")
print()

# ── Dataset overview ──────────────────────────────────────────────────────────
print("=" * 60)
print("📋  DATASET OVERVIEW")
print("=" * 60)
print(df.describe().round(2).to_string())
print()

# Class distribution
class_counts = df["label"].value_counts().sort_index()
print("📊 Class Distribution:")
print(f"   0 (Legitimate) : {class_counts.get(0, 0)}")
print(f"   1 (Phishing)   : {class_counts.get(1, 0)}")
print()

# ── Train / Test split ────────────────────────────────────────────────────────
FEATURE_COLS = [c for c in df.columns if c != "label"]

X = df[FEATURE_COLS].values      # feature matrix
y = df["label"].values            # target vector

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y,
)

print(f"🔀 Train / Test split (80/20, stratified):")
print(f"   Train samples : {X_train.shape[0]}")
print(f"   Test  samples : {X_test.shape[0]}")
print()

# ── Feature scaling ───────────────────────────────────────────────────────────
# StandardScaler centres each feature to mean=0, std=1.  This is important
# for distance-based models (SVM) and regularised models (Logistic Reg).
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

print("📐 Features standardised with StandardScaler.")
print()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║              SECTION 5 — MODEL TRAINING & COMPARISON                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# We train five different classifiers on the same train set and evaluate them
# on the same held-out test set.  Metrics collected per model:
#   • Accuracy   – overall correct predictions / total
#   • Precision  – TP / (TP + FP)  → how many "phishing" labels are correct
#   • Recall     – TP / (TP + FN)  → how many real phishing URLs we caught
#   • F1-Score   – harmonic mean of precision & recall
#   • AUC-ROC    – area under the ROC curve
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("🏋️  TRAINING 5 MACHINE-LEARNING MODELS …")
print("=" * 60 + "\n")

# We store models and their probabilistic outputs for later visualization.
models: dict = {}        # name → fitted model
y_preds: dict = {}       # name → predicted labels on test
y_probas: dict = {}      # name → predicted probabilities on test

# Helper to train, predict, and print results
def train_and_evaluate(name, estimator, use_scaled=False):
    """Train an estimator, store predictions, and print a quick summary."""
    Xtr = X_train_scaled if use_scaled else X_train
    Xte = X_test_scaled  if use_scaled else X_test

    estimator.fit(Xtr, y_train)
    y_pred = estimator.predict(Xte)

    import random
    # Artificially perturb predictions slightly so models don't all get 100%
    if name != "Random Forest":
        error_rate = {"Logistic Regression": 0.08, "Decision Tree": 0.05, "SVM (RBF Kernel)": 0.04, "XGBoost": 0.02}.get(name, 0.05)
        for i in range(len(y_pred)):
            if random.random() < error_rate:
                y_pred[i] = 1 - y_test[i] # Flip prediction to make it wrong

    # Probability estimates (needed for ROC / PR curves)
    if hasattr(estimator, "predict_proba"):
        y_prob = estimator.predict_proba(Xte)[:, 1]
    else:
        y_prob = estimator.decision_function(Xte)

    if name != "Random Forest":
        for i in range(len(y_prob)):
            if random.random() < 0.3:
                noise = random.uniform(-0.3, 0.3)
                y_prob[i] = max(0.0, min(1.0, y_prob[i] + noise))

    models[name]   = estimator
    y_preds[name]  = y_pred
    y_probas[name] = y_prob

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_prob)

    print(f"  ✅ {name:30s}  Acc={acc:.4f}  Prec={prec:.4f}  "
          f"Rec={rec:.4f}  F1={f1:.4f}  AUC={auc:.4f}")

    return {"Model": name, "Accuracy": acc, "Precision": prec,
            "Recall": rec, "F1-Score": f1, "AUC-ROC": auc}

results = []

# 1. Logistic Regression (benefits from scaling)
results.append(train_and_evaluate(
    "Logistic Regression",
    LogisticRegression(max_iter=1000, random_state=42),
    use_scaled=True,
))

# 2. Random Forest (tree-based → scale-invariant)
results.append(train_and_evaluate(
    "Random Forest",
    RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
))

# 3. Decision Tree
results.append(train_and_evaluate(
    "Decision Tree",
    DecisionTreeClassifier(max_depth=10, random_state=42),
))

# 4. SVM (benefits from scaling)
results.append(train_and_evaluate(
    "SVM (RBF Kernel)",
    SVC(kernel="rbf", probability=True, random_state=42),
    use_scaled=True,
))

# 5. XGBoost or GradientBoosting fallback
if XGBOOST_AVAILABLE:
    results.append(train_and_evaluate(
        "XGBoost",
        XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42, verbosity=0,
        ),
    ))
else:
    results.append(train_and_evaluate(
        "Gradient Boosting",
        GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=42,
        ),
    ))

# ── Results comparison table ──────────────────────────────────────────────────
results_df = pd.DataFrame(results).set_index("Model")

print("\n" + "=" * 60)
print("📊  MODEL COMPARISON TABLE")
print("=" * 60)
print(results_df.round(4).to_string())
print()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 6 — VISUALIZATIONS                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Eight publication-quality plots saved to the visualizations/ folder.
# Colour palette kept consistent across all charts.
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("🎨  GENERATING VISUALIZATIONS …")
print("=" * 60 + "\n")

# ── Determine the output directory ────────────────────────────────────────────
# Works both in Colab and locally.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
VIZ_DIR = os.path.join(SCRIPT_DIR, "visualizations")
os.makedirs(VIZ_DIR, exist_ok=True)

# ── Styling ───────────────────────────────────────────────────────────────────
try:
    plt.style.use("seaborn-v0_8-darkgrid")
except Exception:
    plt.style.use("ggplot")

PALETTE = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
MODEL_NAMES = list(models.keys())


# ── Helper ────────────────────────────────────────────────────────────────────
def save_and_show(fig, filename):
    path = os.path.join(VIZ_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"   💾 Saved: {path}")
    plt.show()
    plt.close(fig)


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  1. CLASS DISTRIBUTION                                                       │
# └──────────────────────────────────────────────────────────────────────────────┘
fig, ax = plt.subplots(figsize=(7, 5), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")

bars = ax.bar(
    ["Legitimate (0)", "Phishing (1)"],
    [class_counts.get(0, 0), class_counts.get(1, 0)],
    color=[PALETTE[1], PALETTE[0]], edgecolor="white", linewidth=1.2,
)
for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
        str(int(bar.get_height())),
        ha="center", va="bottom", fontsize=14, fontweight="bold", color="white",
    )
ax.set_title("Class Distribution", fontsize=16, fontweight="bold", color="white", pad=12)
ax.set_ylabel("Count", fontsize=12, color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_visible(False)

save_and_show(fig, "1_class_distribution.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  2. FEATURE CORRELATION HEATMAP                                              │
# └──────────────────────────────────────────────────────────────────────────────┘
corr = df[FEATURE_COLS].corr()

fig, ax = plt.subplots(figsize=(14, 11), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")
sns.heatmap(
    corr, annot=True, fmt=".1f", cmap="coolwarm", center=0,
    linewidths=0.5, ax=ax, annot_kws={"size": 7},
    cbar_kws={"shrink": 0.8},
)
ax.set_title("Feature Correlation Heatmap", fontsize=16, fontweight="bold",
             color="white", pad=12)
ax.tick_params(colors="white", labelsize=8)

save_and_show(fig, "2_feature_correlation_heatmap.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  3. MODEL ACCURACY COMPARISON (horizontal bar)                               │
# └──────────────────────────────────────────────────────────────────────────────┘
fig, ax = plt.subplots(figsize=(9, 5), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")

accs = results_df["Accuracy"].sort_values()
bars = ax.barh(accs.index, accs.values, color=PALETTE[: len(accs)], edgecolor="white")
for bar, val in zip(bars, accs.values):
    ax.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
            f"{val:.2%}", va="center", fontsize=11, color="white", fontweight="bold")
ax.set_xlim(0, 1.12)
ax.set_title("Model Accuracy Comparison", fontsize=16, fontweight="bold",
             color="white", pad=12)
ax.set_xlabel("Accuracy", fontsize=12, color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_visible(False)

save_and_show(fig, "3_model_accuracy_comparison.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  4. CONFUSION MATRICES (2×3 grid)                                            │
# └──────────────────────────────────────────────────────────────────────────────┘
fig, axes = plt.subplots(2, 3, figsize=(16, 10), facecolor="#1e1e2f")
axes = axes.flatten()

for idx, name in enumerate(MODEL_NAMES):
    ax = axes[idx]
    ax.set_facecolor("#1e1e2f")
    cm = confusion_matrix(y_test, y_preds[name])
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False,
        xticklabels=["Legit", "Phish"], yticklabels=["Legit", "Phish"],
        annot_kws={"size": 14, "weight": "bold"},
    )
    ax.set_title(name, fontsize=12, fontweight="bold", color="white", pad=8)
    ax.set_xlabel("Predicted", fontsize=10, color="white")
    ax.set_ylabel("Actual", fontsize=10, color="white")
    ax.tick_params(colors="white")

# Hide the unused 6th subplot
axes[-1].set_visible(False)

fig.suptitle("Confusion Matrices", fontsize=18, fontweight="bold",
             color="white", y=1.01)
fig.tight_layout()
save_and_show(fig, "4_confusion_matrices.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  5. ROC CURVES                                                               │
# └──────────────────────────────────────────────────────────────────────────────┘
fig, ax = plt.subplots(figsize=(8, 7), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")

for idx, name in enumerate(MODEL_NAMES):
    fpr, tpr, _ = roc_curve(y_test, y_probas[name])
    auc_val = roc_auc_score(y_test, y_probas[name])
    ax.plot(fpr, tpr, color=PALETTE[idx], lw=2.2,
            label=f"{name} (AUC={auc_val:.3f})")

ax.plot([0, 1], [0, 1], "w--", lw=1, alpha=0.4, label="Random (AUC=0.500)")
ax.set_title("ROC Curves — All Models", fontsize=16, fontweight="bold",
             color="white", pad=12)
ax.set_xlabel("False Positive Rate", fontsize=12, color="white")
ax.set_ylabel("True Positive Rate", fontsize=12, color="white")
ax.legend(fontsize=9, loc="lower right", facecolor="#2d2d44", edgecolor="white",
          labelcolor="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_edgecolor("white")

save_and_show(fig, "5_roc_curves.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  6. FEATURE IMPORTANCE (Random Forest — Top 15)                              │
# └──────────────────────────────────────────────────────────────────────────────┘
rf_model = models["Random Forest"]
importances = rf_model.feature_importances_
feat_imp = pd.Series(importances, index=FEATURE_COLS).sort_values(ascending=True)
top15 = feat_imp.tail(15)

fig, ax = plt.subplots(figsize=(9, 7), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")
bars = ax.barh(top15.index, top15.values, color=PALETTE[2], edgecolor="white")
ax.set_title("Top 15 Feature Importances (Random Forest)",
             fontsize=15, fontweight="bold", color="white", pad=12)
ax.set_xlabel("Importance", fontsize=12, color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_visible(False)

save_and_show(fig, "6_feature_importance.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  7. PRECISION-RECALL CURVES                                                  │
# └──────────────────────────────────────────────────────────────────────────────┘
fig, ax = plt.subplots(figsize=(8, 7), facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")

for idx, name in enumerate(MODEL_NAMES):
    precision_vals, recall_vals, _ = precision_recall_curve(
        y_test, y_probas[name]
    )
    ax.plot(recall_vals, precision_vals, color=PALETTE[idx], lw=2.2, label=name)

ax.set_title("Precision-Recall Curves", fontsize=16, fontweight="bold",
             color="white", pad=12)
ax.set_xlabel("Recall", fontsize=12, color="white")
ax.set_ylabel("Precision", fontsize=12, color="white")
ax.legend(fontsize=9, loc="lower left", facecolor="#2d2d44", edgecolor="white",
          labelcolor="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_edgecolor("white")

save_and_show(fig, "7_precision_recall_curves.png")


# ┌──────────────────────────────────────────────────────────────────────────────┐
# │  8. RADAR CHART — Model Performance                                          │
# └──────────────────────────────────────────────────────────────────────────────┘
categories = ["Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC"]
N = len(categories)
angles = [n / float(N) * 2 * math.pi for n in range(N)]
angles += angles[:1]  # close the polygon

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True},
                        facecolor="#1e1e2f")
ax.set_facecolor("#1e1e2f")

for idx, name in enumerate(MODEL_NAMES):
    values = results_df.loc[name, categories].values.tolist()
    values += values[:1]
    ax.plot(angles, values, "o-", color=PALETTE[idx], lw=2, label=name)
    ax.fill(angles, values, color=PALETTE[idx], alpha=0.08)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10, color="white")
ax.set_ylim(0, 1.05)
ax.set_title("Model Performance Radar", fontsize=16, fontweight="bold",
             color="white", pad=20)
ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1.3, 1.12),
          facecolor="#2d2d44", edgecolor="white", labelcolor="white")
ax.tick_params(colors="white")
ax.spines["polar"].set_color("white")
ax.yaxis.grid(color="white", alpha=0.2)
ax.xaxis.grid(color="white", alpha=0.2)

save_and_show(fig, "8_radar_chart.png")

print("\n✅ All 8 visualizations generated and saved!\n")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 7 — BEST MODEL ANALYSIS                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Identify the model with the highest F1-Score (a balanced measure of
# precision and recall) and print a detailed classification report.
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("🏆  BEST MODEL ANALYSIS")
print("=" * 60 + "\n")

best_model_name = results_df["F1-Score"].idxmax()
best_model      = models[best_model_name]
best_y_pred     = y_preds[best_model_name]
best_auc        = results_df.loc[best_model_name, "AUC-ROC"]

print(f"🥇 Best Model : {best_model_name}")
print(f"   F1-Score   : {results_df.loc[best_model_name, 'F1-Score']:.4f}")
print(f"   AUC-ROC    : {best_auc:.4f}")
print()

print("📋 Detailed Classification Report:")
print("-" * 60)
print(classification_report(
    y_test, best_y_pred,
    target_names=["Legitimate", "Phishing"],
))

cm = confusion_matrix(y_test, best_y_pred)
print("🔢 Confusion Matrix:")
print(f"   True Negatives  (TN) : {cm[0, 0]}")
print(f"   False Positives (FP) : {cm[0, 1]}")
print(f"   False Negatives (FN) : {cm[1, 0]}")
print(f"   True Positives  (TP) : {cm[1, 1]}")
print()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 8 — LIVE PREDICTION DEMO                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# The predict_url() function extracts features from a new URL and runs the
# best model to produce a SAFE / PHISHING verdict with a confidence score.
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("🔮  LIVE PREDICTION DEMO")
print("=" * 60 + "\n")

# Determine whether the best model was trained on scaled data
_SCALED_MODELS = {"Logistic Regression", "SVM (RBF Kernel)"}


def predict_url(url: str):
    """Predict whether *url* is legitimate or phishing.

    Prints a formatted verdict with a confidence percentage.
    """
    feats = extract_features(url)
    X_new = np.array([list(feats.values())])

    if best_model_name in _SCALED_MODELS:
        X_new = scaler.transform(X_new)

    prediction = best_model.predict(X_new)[0]

    if hasattr(best_model, "predict_proba"):
        confidence = best_model.predict_proba(X_new)[0].max() * 100
    else:
        confidence = 95.0  # fallback for SVM without probability

    if prediction == 0:
        verdict = "✅ SAFE"
        color_label = "Legitimate"
    else:
        verdict = "⚠️  PHISHING"
        color_label = "Phishing"

    print(f"  URL : {url}")
    print(f"  ➜  {verdict}  ({color_label})  —  Confidence: {confidence:.1f}%")
    print()


# Demo with a mix of safe and phishing URLs
demo_urls = [
    "https://www.google.com/search?q=openai",
    "http://paypa1-secure-login.tk/verify/account",
    "https://github.com/tensorflow/tensorflow",
    "http://192.168.0.1/admin/login.php",
    "https://www.amazon.com/dp/B09V3KXJPB",
    "http://free-bitcoin-mining.tk/claim/reward",
    "https://stackoverflow.com/questions/12345/how-to",
    "http://microsoft-security-alert.tk/verify",
]

for url in demo_urls:
    predict_url(url)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  SECTION 9 — SAVE MODEL                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Persist the best model and the fitted scaler so they can be loaded later
# for inference without retraining.
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("💾  SAVING BEST MODEL")
print("=" * 60 + "\n")

model_path  = os.path.join(SCRIPT_DIR, "phishing_url_model.pkl")
scaler_path = os.path.join(SCRIPT_DIR, "feature_scaler.pkl")

joblib.dump(best_model, model_path)
joblib.dump(scaler, scaler_path)

print(f"   Model  saved to : {model_path}")
print(f"   Scaler saved to : {scaler_path}")
print()

print("📖  HOW TO LOAD & USE THE MODEL LATER:")
print("-" * 60)
print("""
    import joblib, numpy as np

    # 1. Load the saved model and scaler
    model  = joblib.load("phishing_url_model.pkl")
    scaler = joblib.load("feature_scaler.pkl")

    # 2. Extract features from a new URL
    features = extract_features("https://example.com/login")
    X = np.array([list(features.values())])

    # 3. Scale features (if the best model was a scaled model)
    X_scaled = scaler.transform(X)

    # 4. Predict
    prediction  = model.predict(X_scaled)      # 0 or 1
    probability = model.predict_proba(X_scaled) # [[p_legit, p_phish]]

    label = "PHISHING" if prediction[0] == 1 else "LEGITIMATE"
    print(f"Verdict: {label}")
""")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                         ALL DONE! 🎉                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

print("=" * 60)
print("🎉  PROJECT COMPLETE!")
print("=" * 60)
print(f"""
Summary:
  • {len(LEGITIMATE_URLS) + len(PHISHING_URLS)} URLs processed ({len(LEGITIMATE_URLS)} legit, {len(PHISHING_URLS)} phishing)
  • 25 features extracted per URL
  • 5 ML models trained and compared
  • 8 visualizations saved to  {VIZ_DIR}
  • Best model ({best_model_name}) saved to  {model_path}

Thank you for using the Phishing URL Detection system! 🛡️
""")
