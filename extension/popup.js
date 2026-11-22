document.addEventListener("DOMContentLoaded", () => {
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const urlInput = document.getElementById("url-input");
    const btnScan = document.getElementById("btn-scan");
    const scanResult = document.getElementById("scan-result");
    const resultBadge = document.getElementById("result-badge");
    const resultConfidence = document.getElementById("result-confidence");
    const resultReasons = document.getElementById("result-reasons");
    const resultTime = document.getElementById("result-time");

    // 1. Check Server Status
    async function checkHealth() {
        try {
            const resp = await fetch("http://127.0.0.1:5000/health", { method: "GET" });
            if (!resp.ok) {
                statusDot.className = "dot offline";
                statusText.textContent = "API Down";
                return;
            }
            const data = await resp.json();
            if (data.queue === "down" || data.status === "degraded") {
                statusDot.className = "dot degraded";
                statusText.textContent = "Queue Down";
            } else {
                statusDot.className = "dot online";
                statusText.textContent = "Online";
            }
        } catch (e) {
            statusDot.className = "dot offline";
            statusText.textContent = "API Down";
        }
    }

    checkHealth();

    // 2. Manual URL Scan
    async function handleScan() {
        const rawUrl = urlInput.value.trim();
        if (!rawUrl) return;

        btnScan.disabled = true;
        btnScan.textContent = "...";

        const startTime = performance.now();
        const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
        const timeoutId = (controller && typeof setTimeout !== "undefined")
            ? setTimeout(() => controller.abort(), 6000)
            : null;

        try {
            const fetchOptions = {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: rawUrl })
            };
            if (controller) fetchOptions.signal = controller.signal;

            const resp = await fetch("http://127.0.0.1:5000/api/v1/assess", fetchOptions);
            if (timeoutId && typeof clearTimeout !== "undefined") clearTimeout(timeoutId);

            const elapsed = (performance.now() - startTime).toFixed(1);

            if (!resp.ok) {
                // If 503 or other server error, show neutral "COULDN'T VERIFY"
                scanResult.classList.remove("hidden");
                resultBadge.textContent = "COULDN'T VERIFY";
                resultBadge.className = "result-badge neutral";
                resultConfidence.textContent = "--";
                resultReasons.innerHTML = `<li>Service unavailable (${resp.status}): queue or worker offline</li>`;
                resultTime.textContent = `${elapsed}ms`;
                return;
            }

            const data = await resp.json();

            // Show result
            scanResult.classList.remove("hidden");
            resultBadge.textContent = data.category.toUpperCase();
            resultBadge.className = data.is_malicious ? "result-badge threat" : "result-badge benign";
            resultConfidence.textContent = `${Math.round(data.confidence * 100)}% match`;
            resultTime.textContent = `${elapsed}ms`;

            resultReasons.innerHTML = "";
            const explanations = data.explanations || [];
            if (explanations.length > 0) {
                explanations.forEach(reason => {
                    const li = document.createElement("li");
                    li.textContent = reason;
                    resultReasons.appendChild(li);
                });
            } else {
                const li = document.createElement("li");
                li.textContent = "No threats detected";
                resultReasons.appendChild(li);
            }
        } catch (err) {
            if (timeoutId && typeof clearTimeout !== "undefined") clearTimeout(timeoutId);
            scanResult.classList.remove("hidden");
            resultBadge.textContent = "COULDN'T VERIFY";
            resultBadge.className = "result-badge neutral";
            resultConfidence.textContent = "--";
            const msg = err.name === "AbortError" ? "Assessment timed out" : (err.message || "Could not contact server");
            resultReasons.innerHTML = `<li>${msg}</li>`;
            resultTime.textContent = "--";
        } finally {
            btnScan.disabled = false;
            btnScan.textContent = "Scan";
        }
    }

    btnScan.addEventListener("click", handleScan);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleScan();
    });
});
