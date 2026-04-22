#!/usr/bin/env python3
"""
Buy an InsumerAPI key with USDC, USDT, or BTC (agent-onboarding path).

Path 3 of 4 (see ../SKILL.md). No email required — sender wallet from the
on-chain transaction becomes the key's identity. Send funds to the platform
wallet first, then call this with the resulting transaction hash.

Platform wallets:
  EVM:     0xAd982CB19aCCa2923Df8F687C0614a7700255a23
  Solana:  6a1mLjefhvSJX1sEX8PTnionbE9DqoYjU6F6bNkT4Ydr
  Bitcoin: bc1qg7qnerdhlmdn899zemtez5tcx2a2snc0dt9dt0

Volume discounts: $5–$99 → $0.04/call, $100–$499 → $0.03/call (25% off),
                  $500+ → $0.02/call (50% off).

The appName is hard-coded to "insumer-agent-skills" for distribution-channel
attribution. Override with --app-name only if you have a specific reason —
otherwise leave it so origin funnel tracking works.

Usage:
    python buy_key.py --tx 0xabc... --chain 8453 --amount 10
    python buy_key.py --tx <btc-tx> --chain bitcoin
    python buy_key.py --tx 0xabc... --chain 8453 --amount 10 --app-name my-custom-name
"""
import argparse
import json
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://api.insumermodel.com/v1/keys/buy"
DEFAULT_APP_NAME = "insumer-agent-skills"


def main() -> int:
    parser = argparse.ArgumentParser(description="Buy an InsumerAPI key with crypto.")
    parser.add_argument("--tx", required=True, help="Transaction hash proving payment")
    parser.add_argument("--chain", required=True, help="Chain ID (e.g. 8453 for Base, 'solana', 'bitcoin')")
    parser.add_argument("--amount", type=float, help="Stablecoin amount sent (min 5). Optional for BTC.")
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME,
                        help=f"App name (default: {DEFAULT_APP_NAME!r}, for funnel tracking)")
    args = parser.parse_args()

    chain = int(args.chain) if args.chain.isdigit() else args.chain

    body_dict = {
        "txHash": args.tx,
        "chainId": chain,
        "appName": args.app_name,
    }
    if args.amount is not None:
        body_dict["amount"] = args.amount

    body = json.dumps(body_dict).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return 1

    data = payload.get("data", {})
    key = data.get("key")
    if not key:
        print("Unexpected response:", json.dumps(payload, indent=2), file=sys.stderr)
        return 1

    print(f"\nKey purchased for {data.get('registeredWallet')}")
    print(f"  Tier:           {data.get('tier')}")
    print(f"  Daily limit:    {data.get('dailyLimit')}")
    print(f"  Credits added:  {data.get('creditsAdded')}")
    print(f"  Total credits:  {data.get('totalCredits')}")
    print(f"  USDC paid:      ${data.get('usdcPaid')} ({data.get('chainName')})")
    print(f"  Effective rate: {data.get('effectiveRate')}")
    print(f"\nStore this key securely (shown only once):\n")
    print(f"    export INSUMER_API_KEY='{key}'\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
