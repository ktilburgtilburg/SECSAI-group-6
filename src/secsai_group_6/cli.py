import argparse
import os
import sys

import requests

# Exit codes: 0 = clean, 1 = threat found, 2 = error
EXIT_CLEAN, EXIT_THREAT, EXIT_ERROR = 0, 1, 2
TIMEOUT_S = 5


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, query the assessment API, and print the verdict."""
    parser = argparse.ArgumentParser(
        prog="secsai", description="Check a URL for threats."
    )
    parser.add_argument("--check", required=True, metavar="URL", help="URL to assess")
    parser.add_argument(
        "--api",
        default=os.environ.get("SECSAI_API_URL", "http://127.0.0.1:5000"),
        help="base URL of the API server",
    )
    args = parser.parse_args(argv)

    try:
        resp = requests.post(
            f"{args.api}/api/v1/assess", json={"url": args.check}, timeout=TIMEOUT_S
        )
    except requests.RequestException as exc:
        print(
            f"error: cannot reach the API at {args.api} ({type(exc).__name__})",
            file=sys.stderr,
        )
        return EXIT_ERROR

    try:
        data = resp.json()
    except ValueError:
        print(
            f"error: API returned a non-JSON response (HTTP {resp.status_code})",
            file=sys.stderr,
        )
        return EXIT_ERROR

    if resp.status_code != 200:
        print(
            f"error: {data.get('error', 'unknown error')} (HTTP {resp.status_code})",
            file=sys.stderr,
        )
        return EXIT_ERROR

    verdict = "MALICIOUS" if data["is_malicious"] else "SAFE"
    print(f"{verdict}: {data['category']} ({data['confidence']:.0%} confidence)")
    for reason in data["explanations"]:
        print(f"  - {reason}")
    return EXIT_THREAT if data["is_malicious"] else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
