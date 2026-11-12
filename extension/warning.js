document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);

    // Read parameters from URL (or use realistic test fallbacks)
    const targetUrl = params.get("url") || "https://example-phishing-login.com/auth";
    const category = params.get("category") || "phishing";
    const confidence = parseFloat(params.get("confidence") || "0.88");

    let explanations = [];
    try {
        explanations = JSON.parse(params.get("explanations") || '[]');
    } catch (e) {
        explanations = [];
    }

    if (explanations.length === 0) {
        explanations = ["Contains credential keywords", "Hostname randomness is high"];
    }

    // Populate UI elements
    document.getElementById("threat-badge").textContent = category.toUpperCase();
    document.getElementById("confidence-level").textContent = `${Math.round(confidence * 100)}% Confidence`;
    document.getElementById("blocked-url").textContent = targetUrl;

    const reasonsList = document.getElementById("reasons-list");
    reasonsList.innerHTML = "";
    explanations.forEach(reason => {
        const li = document.createElement("li");
        li.textContent = reason;
        reasonsList.appendChild(li);
    });

    // 1. Cancel & Go Back Button
    document.getElementById("btn-back").addEventListener("click", () => {
        if (window.history.length > 2) {
            // Skip the blocked page in history and go back to the safe page before it
            window.history.go(-2);
        } else if (document.referrer && !document.referrer.includes(targetUrl)) {
            window.location.href = document.referrer;
        } else {
            // Fallback: safe home page or close tab
            window.location.href = "https://www.google.com";
        }
    });

    // 2. Proceed Anyway (Bypass) Button
    document.getElementById("btn-bypass").addEventListener("click", () => {
        if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
            chrome.runtime.sendMessage({ action: "bypass", url: targetUrl }, () => {
                window.location.href = targetUrl;
            });
        } else {
            window.location.href = targetUrl;
        }
    });

    // 3. Report Mistake Button
    document.getElementById("btn-feedback").addEventListener("click", async () => {
        const statusEl = document.getElementById("feedback-message");
        statusEl.textContent = "Submitting feedback...";
        try {
            const resp = await fetch("http://127.0.0.1:5000/api/v1/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: targetUrl,
                    shown_category: category,
                    reported_category: "benign"
                })
            });
            if (resp.ok) {
                statusEl.textContent = "Thank you! Feedback recorded.";
            } else {
                statusEl.textContent = "Feedback submission failed.";
            }
        } catch (err) {
            statusEl.textContent = "Could not reach server to submit feedback.";
        }
    });
});
