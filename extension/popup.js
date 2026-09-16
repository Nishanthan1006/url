// Get the current tab's URL and display it
document.addEventListener('DOMContentLoaded', function () {
    const urlInput = document.getElementById('url-input');

    // Auto-fill if running inside Chrome extension
    if (typeof chrome !== 'undefined' && chrome.tabs) {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs && tabs[0]) {
                urlInput.value = tabs[0].url;
            }
        });
    }

    document.getElementById('scan-btn').addEventListener('click', function () {
        const url = urlInput.value.trim();
        if (url) scanURL(url);
    });

    urlInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const url = urlInput.value.trim();
            if (url) scanURL(url);
        }
    });
});

function scanURL(url) {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    document.getElementById('xai-container').style.display = 'none';

    const btn = document.getElementById('scan-btn');
    btn.disabled = true;
    btn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation:spin 1s linear infinite">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        Analyzing...
    `;

    // Ensure spin keyframe exists
    if (!document.getElementById('spin-style')) {
        const s = document.createElement('style');
        s.id = 'spin-style';
        s.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
        document.head.appendChild(s);
    }

    // 🌐 Production API URL (deployed on Render)
    const API_BASE = 'https://url-2ejq.onrender.com';
    fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url }),
    })
    .then(r => r.json())
    .then(data => displayResult(data))
    .catch(err => displayError(err))
    .finally(() => {
        document.getElementById('loading').style.display = 'none';
        btn.disabled = false;
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Analyze URL
        `;
    });
}

function displayResult(data) {
    const resultBox = document.getElementById('result');
    const predictionEl = document.getElementById('prediction');
    const descEl = document.getElementById('result-desc');
    const iconEl = document.getElementById('result-icon');
    const confidenceEl = document.getElementById('confidence');
    const barEl = document.getElementById('confidence-bar');

    resultBox.style.display = 'block';
    const pct = parseFloat(data.confidence);

    if (data.prediction === 'PHISHING') {
        resultBox.className = 'result-phishing';
        iconEl.textContent = '🚨';
        predictionEl.textContent = 'PHISHING DETECTED';
        descEl.textContent = 'This URL exhibits suspicious characteristics';
    } else {
        resultBox.className = 'result-safe';
        iconEl.textContent = '✅';
        predictionEl.textContent = 'SAFE URL';
        descEl.textContent = 'This URL appears to be legitimate';
    }

    confidenceEl.textContent = `${pct}%`;

    // Animate confidence bar
    requestAnimationFrame(() => {
        setTimeout(() => { barEl.style.width = pct + '%'; }, 50);
    });

    // XAI Section
    if (data.explainable_ai && data.explainable_ai.length > 0) {
        const xaiContainer = document.getElementById('xai-container');
        const xaiList = document.getElementById('xai-list');
        xaiList.innerHTML = '';

        data.explainable_ai.forEach(item => {
            const div = document.createElement('div');
            div.className = `xai-item ${item.color}`;
            div.innerHTML = `
                <div style="flex:1;display:flex;align-items:center;">
                    <span class="xai-feature-name">${item.feature}</span>
                    <span class="xai-feature-val">${item.value}</span>
                </div>
                <span class="xai-impact">${item.impact.replace(' Phishing Risk', '').replace('Increases', '↑ Risk').replace('Decreases', '↓ Risk')}</span>
            `;
            xaiList.appendChild(div);
        });

        xaiContainer.style.display = 'block';
    }
}

function displayError(error) {
    const resultBox = document.getElementById('result');
    resultBox.style.display = 'block';
    resultBox.className = '';
    resultBox.style.cssText = 'display:block; margin:0 20px 16px; border-radius:14px; padding:16px; background:rgba(255,179,71,0.1); border:1.5px solid rgba(255,179,71,0.3);';
    resultBox.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">⚠️</span>
            <div>
                <div style="font-size:13px;font-weight:700;color:#ffb347;margin-bottom:4px;">Cannot connect to server</div>
                <div style="font-size:11px;color:#6b7a99;">Ensure the backend API is online and reachable.</div>
            </div>
        </div>
    `;
}
