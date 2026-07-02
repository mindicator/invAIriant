# The change

> ILLUSTRATIVE / SYNTHESIZED diff. PR #874 — "feat(api): generate CRUD handlers
> for orders, invoices, shipments" (+1,612 / −40, 22 files). The handlers were
> generated from one template and are near-identical — which is exactly why the
> one that diverges is hard to see. Two of the four resource modules are shown.

```diff
--- a/src/routes/orders.ts
+++ b/src/routes/orders.ts
@@ -0,0 +1,26 @@
+import { Router } from "express";
+import { requireAuth } from "../mw/auth";
+import { requireTenantScope } from "../mw/authz";
+import { OrdersRepo } from "../repos/orders";
+
+export const orders = Router();
+
+orders.get("/:id", requireAuth, requireTenantScope("orders:read"), async (req, res) => {
+  const row = await OrdersRepo.byId(req.params.id, req.tenantId);
+  if (!row) return res.status(404).json({ error: "not_found" });
+  return res.json(row);
+});

--- a/src/routes/invoices.ts
+++ b/src/routes/invoices.ts
@@ -0,0 +1,26 @@
+import { Router } from "express";
+import { requireAuth } from "../mw/auth";
+import { requireTenantScope } from "../mw/authz";
+import { InvoicesRepo } from "../repos/invoices";
+
+export const invoices = Router();
+
+// NOTE: generated from the same template as orders.ts
+invoices.get("/:id", requireAuth, async (req, res) => {
+  // requireTenantScope("invoices:read") omitted — the generator dropped it here
+  const row = await InvoicesRepo.byId(req.params.id, req.tenantId);
+  if (!row) return res.status(404).json({ error: "not_found" });
+  return res.json(row);
+});
```
