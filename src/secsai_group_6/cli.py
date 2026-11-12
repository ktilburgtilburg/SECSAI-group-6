import argparse
import sys

from secsai_group_6.backend.validation import InvalidInput, clean_url
from secsai_group_6.ml import predict

# Exit codes: 0 = clean, 1 = threat found, 2 = error
EXIT_CLEAN, EXIT_THREAT, EXIT_ERROR = 0, 1, 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="secsai", description="Check a URL for threats."
    )
    parser.add_argument("--check", required=True, metavar="URL", help="URL to assess")
    args = parser.parse_args(argv)

    try:
        url = clean_url(args.check)
        result = predict(url)
    except InvalidInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:
        print(f"error: prediction fialed ({exc})", file=sys.stderr)
        return EXIT_ERROR

    verdict = "MALICIOUS" if result["is_malicious"] else "SAFE"
    print(f"{verdict}: {result['category']} ({result['confidence']:.0%} confidence)")
    for reason in result["explanations"]:
        print(f"  - {reason}")
    return EXIT_THREAT if result["is_malicious"] else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
