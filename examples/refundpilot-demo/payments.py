"""Thin wrapper over the payments provider. issue_payout moves real money."""

import os
import requests

_API = "https://payments.internal/v1/payouts"


def issue_payout(customer_id, amount_usd):
    """Send `amount_usd` to the customer. There is NO server-side cap — the
    caller is trusted to have authorized the amount."""
    resp = requests.post(
        _API,
        headers={"Authorization": f"Bearer {os.environ['PAYMENTS_TOKEN']}"},
        json={"customer_id": customer_id, "amount": amount_usd, "currency": "USD"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["payout_id"]
