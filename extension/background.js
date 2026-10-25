function isInternalOrLocalWeb(urlString) {
    try {
        const parsed = new URL(urlString);

        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return true;
        }
        if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            return true;
        }

        // Not internal or local!
        return false;
    } catch (error) {
        // If it failed to parse as a URL, treat it as internal/ignore
        return true;
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
});
