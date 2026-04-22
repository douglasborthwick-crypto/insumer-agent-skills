#!/usr/bin/env python3
"""
Top up an existing InsumerAPI key with credits via on-chain payment.

Path 4 of 4 (see ../SKILL.md). Preserves key, history, tier, and integrations
— credits just increment. Send funds to the platform wallet first, then call
this with the transaction hash. Sender must match the wallet registered to the
key (or pass --update-wallet to replace it).

Usage:
    python buy_credits.py --tx 0xabc... --chain 8453 --amount 10
    python buy_credits.py --tx 0xabc... --chain 8453 --amount 100 --update-wallet
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://api.insumermodel.com/v1/credits/buy"


def main() -> int:
    parser = argparse.ArgumentParser(description="Top up an InsumerAPI key with crypto.")
    parser.add_argument("--tx", required=True, help="Transaction hash proving payment")
    parser.add_argument("--chain", required=True, help="Chain ID (e.g. 8453 for Base, 'solana', 'bitcoin')")
    parser.add_argument("--amount", type=float, help="Stablecoin amount sent (min 5). Optional for BTC.")
    parser.add_argument("--update-wallet", action="store_true",
                        help="Replace the registered sender wallet with this transaction's sender")
    args = parser.parse_args()

    api_key = os.environ.get("INSUMER_API_KEY")
    if not api_key:
        print("INSUMER_API_KEY not set. See the insumer-auth skill.", file=sys.stderr)
        return 1

    chain = int(args.chain) if args.chain.isdigit() else args.chain

    body_dict = {
        "txHash": args.tx,
        "chainId": chain,
    }
    if args.amount is not None:
        body_dict["amount"] = args.amount
    if args.update_wallet:
        body_dict["updateWallet"] = True

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
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return 1

    data = payload.get("data", {})
    print(f"\nCredits topped up")
    print(f"  Credits added:  {data.get('creditsAdded')}")
    print(f"  Total credits:  {data.get('totalCredits')}")
    print(f"  USDC paid:      ${data.get('usdcPaid')} ({data.get('chainName')})\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
