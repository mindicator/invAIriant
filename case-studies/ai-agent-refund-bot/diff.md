# The change

> ILLUSTRATIVE / SYNTHESIZED diff. PR #218 — "feat(agent): let the support
> agent issue refunds end-to-end". Wires the LLM's structured decision
> straight into the payment provider's refund call.

```diff
--- a/agent/refund_tool.py
+++ b/agent/refund_tool.py
@@ -18,10 +18,34 @@ from agent.llm import chat
 from payments.provider import StripeClient
 
 REFUND_PROMPT = """You are a support agent. Given the ticket and the order,
-decide whether a refund is warranted. Explain your reasoning.
+decide whether a refund is warranted and the amount in cents. Respond as JSON:
+{"refund": true|false, "amount_cents": <int>, "reason": "<text>"}.
 """
 
-def draft_refund_reply(ticket: Ticket, order: Order) -> str:
-    """Draft a reply for a human agent to review before any money moves."""
-    reasoning = chat(REFUND_PROMPT, ticket=ticket, order=order)
-    return reasoning  # human decides + executes the refund in the console
+def decide_and_refund(ticket: Ticket, order: Order) -> RefundResult:
+    """Agent decides and executes the refund in one pass."""
+    raw = chat(REFUND_PROMPT, ticket=ticket, order=order)
+    try:
+        decision = json.loads(raw)
+    except json.JSONDecodeError:
+        # Model usually returns clean JSON; fall back to the raw string.
+        log.warning("refund decision not valid JSON, retrying once")
+        raw = chat(REFUND_PROMPT, ticket=ticket, order=order)
+        decision = json.loads(raw)
+
+    if not decision.get("refund"):
+        return RefundResult(refunded=False, reason=decision.get("reason", ""))
+
+    # Execute against the provider. amount_cents comes straight from the model.
+    result = StripeClient().refund(
+        charge_id=order.charge_id,
+        amount_cents=decision["amount_cents"],
+        idempotency_key=None,
+        reason=decision.get("reason", "support agent refund"),
+    )
+    log.info("refund issued", extra={"order": order.id, "amount": decision["amount_cents"]})
+    return RefundResult(refunded=True, amount_cents=decision["amount_cents"])
```
