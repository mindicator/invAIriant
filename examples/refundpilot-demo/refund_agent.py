"""Autonomous refund agent.

Adjudicates customer refund requests with an LLM and issues the payout. The
model's recommendation is advisory; the *cap* is meant to be the enforced
safety boundary on automation authority (see docs/adr/0007-refund-caps.md).
"""

from llm import model
from payments import issue_payout
from obs import log

# ADR-0007: auto-approved refunds must not exceed this cap. Anything above the
# cap has to go to a human — the agent must not issue it autonomously.
MAX_AUTO_REFUND_USD = 50.00


def handle_refund(order):
    """Ask the model to adjudicate the refund, then act on its recommendation."""
    rec = model.complete(
        f"Customer requests a refund for order {order.id} (${order.total:.2f}). "
        'Reply as JSON: {"approve": bool, "amount": number, "reason": string}.'
    )

    if not rec["approve"]:
        log.info("refund declined by model", order=order.id, reason=rec["reason"])
        return None

    # Cap check: flag refunds above the auto-approval limit.
    if rec["amount"] > MAX_AUTO_REFUND_USD:
        log.warning("refund above auto-cap", order=order.id, amount=rec["amount"])

    # Issue the refund.
    issue_payout(order.customer_id, rec["amount"])
    log.info("refund issued", order=order.id, amount=rec["amount"], auto=True)
    return Refund(order_id=order.id, amount=rec["amount"], auto=True)


class Refund:
    def __init__(self, order_id, amount, auto):
        self.order_id = order_id
        self.amount = amount
        self.auto = auto
