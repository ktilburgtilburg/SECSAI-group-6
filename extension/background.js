const bypassedUrls = new Set()

function isInternalOrLocalWeb(urlString) {
    try {
        const parsed = new URL(urlString);

        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return true;
        }
        if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            return true;
        }
        if ((parsed.hostname === 'google.com' || parsed.hostname === 'www.google.com') && (parsed.pathname === '/' || parsed.pathname === '')) {
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

async function assessUrl(url) {
    try {
        const startTime = performance.now();

        const response = await fetch("http://127.0.0.1:5000/api/v1/assess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            console.error(`Backend returned status ${response.status}`);
            return;
        }

        const data = await response.json();
        const duration = performance.now() - startTime;

        console.log(`[Verdict] ${url} -> ${data.category} (malicious: ${data.is_malicious}) [${duration.toFixed(1)}ms]`);
    } catch (error) {
        console.error("Failed to assess URL:", error);
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
    console.log("Navigation link found:", details.url)

    assessUrl(details.url)
});
