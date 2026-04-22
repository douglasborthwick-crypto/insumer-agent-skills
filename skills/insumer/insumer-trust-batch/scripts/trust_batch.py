#!/usr/bin/env python3
"""
Call POST /v1/trust/batch for multiple wallets in one request.

Reads INSUMER_API_KEY from env. Each wallet costs 3 credits (or 6 with merkle).

Usage:
    python trust_batch.py --wallets 0xabc...,0xdef...
    python trust_batch.py --wallets-file allowlist.txt
    python trust_batch.py --wallets-file allowlist.txt --proof merkle
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://api.insumermodel.com/v1/trust/batch"


def main() -> int:
    parser = argparse.ArgumentParser(description="POST /v1/trust/batch")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wallets", help="Comma-separated wallet list (e.g. 0xabc...,0xdef...)")
    group.add_argument("--wallets-file", help="Path to file with one wallet per line")
    parser.add_argument("--proof", choices=["merkle"],
                        help="Set 'merkle' for EIP-1186 proofs (6 credits/wallet)")
    args = parser.parse_args()

    api_key = os.environ.get("INSUMER_API_KEY")
    if not api_key:
        print("INSUMER_API_KEY not set. See the insumer-auth skill.", file=sys.stderr)
        return 1

    if args.wallets:
        wallets = [w.strip() for w in args.wallets.split(",") if w.strip()]
    else:
        with open(args.wallets_file) as f:
            wallets = [line.strip() for line in f if line.strip()]

    if not wallets:
        print("No wallets provided.", file=sys.stderr)
        return 1

    body_dict = {"wallets": wallets}
    if args.proof:
        body_dict["proof"] = args.proof

    body = json.dumps(body_dict).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
