import ipaddress
from urllib.parse import urlparse

import tldextract

try:
    import Levenshtein as _Lev
    def _lev(a, b): return _Lev.distance(a, b)
except ImportError:
    def _lev(a, b):
        if a == b: return 0
        la, lb = len(a), len(b)
        if not la: return lb
        if not lb: return la
        prev = list(range(lb + 1))
        for i, ca in enumerate(a, 1):
            cur = [i] + [0] * lb
            for j, cb in enumerate(b, 1):
                cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            prev = cur
        return prev[lb]


_extractor = tldextract.TLDExtract(suffix_list_urls=())
_SCHEME_PREFIXES = ("https://", "http://", "//")

SENSITIVE_WORDS = (
    "login", "log-in", "signin", "sign-in", "verify", "verification",
    "confirm", "password", "credential", "bank", "banking", "wallet",
    "secure", "security", "unlock", "suspend", "suspended", "reactivate",
    "passcode", "otp",
)

KNOWN_BRANDS = {
    "google.com": "google", "youtube.com": "youtube", "gmail.com": "gmail",
    "amazon.com": "amazon", "apple.com": "apple", "icloud.com": "icloud",
    "microsoft.com": "microsoft", "office.com": "office", "office365.com": "office365",
    "outlook.com": "outlook", "live.com": "live", "paypal.com": "paypal",
    "netflix.com": "netflix", "facebook.com": "facebook", "instagram.com": "instagram",
    "whatsapp.com": "whatsapp", "linkedin.com": "linkedin", "twitter.com": "twitter",
    "x.com": "x", "github.com": "github", "gitlab.com": "gitlab",
    "dropbox.com": "dropbox", "adobe.com": "adobe", "yahoo.com": "yahoo",
    "wikipedia.org": "wikipedia", "chase.com": "chase", "wellsfargo.com": "wellsfargo",
    "bankofamerica.com": "bankofamerica", "binance.com": "binance", "coinbase.com": "coinbase",
    "steamcommunity.com": "steamcommunity", "steampowered.com": "steampowered",
    "spotify.com": "spotify", "zoom.us": "zoom", "telegram.org": "telegram",
    "dhl.com": "dhl", "fedex.com": "fedex", "ups.com": "ups",
}

_BRAND_TOKENS = frozenset(KNOWN_BRANDS.values())
_BRAND_DOMAINS = frozenset(KNOWN_BRANDS.keys())

_TLD_RISK = {
    "gov": 0.05, "edu": 0.05, "mil": 0.05, "int": 0.05, "gov.uk": 0.05,
    "gov.au": 0.05, "gouv.fr": 0.05, "gc.ca": 0.05, "ac.uk": 0.05,
    "edu.au": 0.05, "gob.es": 0.05, "gov.it": 0.05,
    "com": 0.10, "org": 0.10, "net": 0.10,
    "de": 0.20, "fr": 0.20, "uk": 0.20, "co.uk": 0.20, "org.uk": 0.20,
    "nl": 0.20, "it": 0.20, "ca": 0.20, "au": 0.20, "com.au": 0.20,
    "jp": 0.20, "es": 0.20, "be": 0.20, "ch": 0.20, "at": 0.20,
    "ie": 0.20, "nz": 0.20, "eu": 0.20, "us": 0.20, "io": 0.20,
    "co": 0.20, "ai": 0.20, "app": 0.20, "dev": 0.20, "me": 0.20, "fm": 0.20,
    "se": 0.30, "no": 0.30, "fi": 0.30, "dk": 0.30, "kr": 0.30,
    "pt": 0.30, "pl": 0.30, "cz": 0.30, "ro": 0.30, "gr": 0.30,
    "hu": 0.30, "sk": 0.30, "tech": 0.30, "cloud": 0.30, "systems": 0.30,
    "network": 0.30, "software": 0.30, "codes": 0.30, "is": 0.30,
    "gg": 0.30, "asia": 0.30,
    "br": 0.40, "com.br": 0.40, "in": 0.40, "cn": 0.40, "com.cn": 0.40,
    "ru": 0.40, "mx": 0.40, "com.mx": 0.40, "cl": 0.40, "vn": 0.40,
    "com.vn": 0.40, "za": 0.40, "co.za": 0.40, "ar": 0.40, "com.ar": 0.40,
    "ua": 0.40, "com.ua": 0.40, "ir": 0.40,
    "online": 0.50, "site": 0.50, "info": 0.50, "biz": 0.50,
    "pro": 0.50, "cc": 0.50, "tv": 0.50, "ly": 0.50,
    "work": 0.60, "zip": 0.60, "mov": 0.60, "country": 0.60,
    "stream": 0.60, "science": 0.60, "party": 0.60, "men": 0.60,
    "to": 0.60, "ws": 0.60,
    "xyz": 0.70, "top": 0.70, "click": 0.70, "loan": 0.70,
    "gdn": 0.70, "icu": 0.70,
    "tk": 0.85, "ml": 0.85, "ga": 0.85, "cf": 0.85, "gq": 0.85,
}
_TLD_RISK_DEFAULT = 0.40


def strip_url(url: str) -> str:
    if not isinstance(url, str):
        return ""
    u = url.strip()
    low = u.lower()
    for p in _SCHEME_PREFIXES:
        if low.startswith(p):
            u = u[len(p):]
            break
    slash = u.find("/")
    if slash == -1:
        host, rest = u, ""
    else:
        host, rest = u[:slash], u[slash:]
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    rest = rest.rstrip("/")
    return host + rest


def extract_features(url: str) -> dict:
    u = strip_url(url)
    try:
        parts = urlparse("//" + u)
    except ValueError:
        parts = urlparse("//")
    try:
        has_port = parts.port is not None
    except ValueError:
        has_port = False
    ext = _extractor(u)
    try:
        hostname = (parts.hostname or ext.fqdn or "").lower()
    except ValueError:
        hostname = (ext.fqdn or "").lower()
    path = parts.path or ""
    query = parts.query or ""
    subdomain = (ext.subdomain or "").lower()
    tld = (ext.suffix or "").lower()
    registrable = (f"{ext.domain}.{tld}" if tld else ext.domain).lower()

    url_length = len(u)
    digit_count = sum(c.isdigit() for c in u)
    combined_text = (hostname + " " + path + " " + query).lower()
    sensitive_count = sum(combined_text.count(w) for w in SENSITIVE_WORDS)
    num_subdomains = len(subdomain.split(".")) if subdomain else 0

    if registrable:
        dist_to_brand = min(_lev(registrable, bd) for bd in _BRAND_DOMAINS)
    else:
        dist_to_brand = min(_lev(hostname, bd) for bd in _BRAND_DOMAINS)

    is_exact_brand = 1.0 if registrable in _BRAND_DOMAINS else 0.0

    if not is_exact_brand and subdomain:
        toks = {c for c in subdomain.replace("-", ".").split(".") if c}
        brand_in_sub = 1.0 if (toks & _BRAND_TOKENS) else 0.0
        num_brand_matches = len(toks & _BRAND_TOKENS)
    else:
        brand_in_sub = 0.0
        num_brand_matches = 0

    edit_distance_normalized = (
        float(dist_to_brand) / max(len(registrable), 1) if registrable else 0.0
    )

    tld_risk = _TLD_RISK.get(tld, _TLD_RISK_DEFAULT) if tld else 0.0

    is_ip_host = False
    try:
        ipaddress.ip_address(hostname.strip("[]"))
        is_ip_host = True
    except ValueError:
        pass

    return {
        "url_length": url_length,
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": u.count("."),
        "num_hyphens": u.count("-"),
        "num_slashes": u.count("/"),
        "num_at": u.count("@"),
        "num_question": u.count("?"),
        "num_equals": u.count("="),
        "num_digits": digit_count,
        "num_underscores": u.count("_"),
        "num_special_chars": sum(not c.isalnum() for c in u),
        "digit_ratio": digit_count / url_length if url_length else 0.0,
        "is_ip_host": is_ip_host,
        "has_port": has_port,
        "has_punycode": "xn--" in hostname,
        "num_subdomains": num_subdomains,
        "num_query_params": len(query.split("&")) if query else 0,
        "tld_risk": tld_risk,
        "edit_distance_to_nearest_brand": float(dist_to_brand),
        "edit_distance_normalized": edit_distance_normalized,
        "is_exact_brand_domain": is_exact_brand,
        "brand_in_subdomain_not_registrable": brand_in_sub,
        "num_subdomain_brand_matches": num_brand_matches,
        "has_sensitive_word": sensitive_count > 0,
        "num_sensitive_words": sensitive_count,
    }


def feature_names() -> list[str]:
    return list(extract_features("example.com").keys())


if __name__ == "__main__":
    for u in ["google.com", "gooogle.com", "paypal.com.secure-login.net",
              "192.168.1.1/login", "google.com/search?q=test"]:
        f = extract_features(u)
        print(f"\n{u!r}")
        print(f"  edit_norm:    {f['edit_distance_normalized']:.3f}")
        print(f"  brand_in_sub: {f['brand_in_subdomain_not_registrable']:.0f}")
        print(f"  tld_risk:     {f['tld_risk']:.2f}")
        print(f"  sensitive:    {f['num_sensitive_words']}")