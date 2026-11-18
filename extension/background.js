const bypassedUrls = new Set();

function isInternalOrLocalWeb(urlString) {
    try {
        const parsed = new URL(urlString);

        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return true;
        }
        if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            return true;
        }
        if (parsed.hostname === 'google.com' || parsed.hostname.endsWith('.google.com')) {
            return true;
        }

        if (bypassedUrls.has(urlString)) {
            return true;
        }

        // Not internal or local!
        return false;
    } catch (error) {
        // If it failed to parse as a URL, treat it as internal/ignore
        return true;
    }
}

function updateBadge(tabId, text, color, title) {
    if (typeof chrome !== "undefined" && chrome.action) {
        if (chrome.action.setBadgeText) {
            chrome.action.setBadgeText({ text: text || "", tabId: tabId });
        }
        if (color && chrome.action.setBadgeBackgroundColor) {
            chrome.action.setBadgeBackgroundColor({ color: color, tabId: tabId });
        }
        if (title && chrome.action.setTitle) {
            chrome.action.setTitle({ title: title, tabId: tabId });
        }
    }
}

async function assessUrl(url, tabId) {
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timeoutId = (controller && typeof setTimeout !== "undefined")
        ? setTimeout(() => controller.abort(), 5000)
        : null;

    try {
        const startTime = performance.now();

        const fetchOptions = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        };
        if (controller) {
            fetchOptions.signal = controller.signal;
        }

        const response = await fetch("http://127.0.0.1:5000/api/v1/assess", fetchOptions);
        if (timeoutId && typeof clearTimeout !== "undefined") {
            clearTimeout(timeoutId);
        }

        if (!response.ok) {
            console.error(`Backend returned status ${response.status}`);
            // Neutral "couldn't verify" badge, never block navigation
            updateBadge(tabId, "?", "#6b7280", "Couldn't verify URL (backend status " + response.status + ")");
            return;
        }

        const data = await response.json();
        const duration = performance.now() - startTime;

        if (data.is_malicious) {
            console.warn(`[BLOCKED] Threat detected on tab ${tabId}: ${url}`);
            updateBadge(tabId, "!", "#ef4444", `Threat detected: ${data.category}`);

            const baseUrl = (chrome.runtime && chrome.runtime.getURL)
                ? chrome.runtime.getURL("warning.html")
                : "warning.html";

            const warningUrl = baseUrl +
                `?url=${encodeURIComponent(url)}` +
                `&category=${encodeURIComponent(data.category)}` +
                `&confidence=${encodeURIComponent(data.confidence)}` +
                `&explanations=${encodeURIComponent(JSON.stringify(data.explanations || []))}`;

            if (chrome.tabs && chrome.tabs.update) {
                chrome.tabs.update(tabId, { url: warningUrl });
            }
        } else {
            updateBadge(tabId, "", "#22c55e", "Verified safe");
        }

        console.log(`[Verdict] ${url} -> ${data.category} (malicious: ${data.is_malicious}) [${duration.toFixed(1)}ms]`);

    } catch (error) {
        if (timeoutId && typeof clearTimeout !== "undefined") {
            clearTimeout(timeoutId);
        }
        console.error("Failed to assess URL:", error);
        // Neutral "couldn't verify" badge, never block or crash navigation
        updateBadge(tabId, "?", "#6b7280", "Couldn't verify URL");
    }
}

chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    // details contains information about the navigation
    if (details.frameId !== 0) {
        return;
    }

    if (isInternalOrLocalWeb(details.url)) {
        console.log("Ignored internal/local URL:", details.url);
        return;
    }
    console.log("Navigation link found:", details.url);

    assessUrl(details.url, details.tabId);
});

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "bypass" && message.url) {
            bypassedUrls.add(message.url);
            sendResponse({ success: true });
        }
    });
}
