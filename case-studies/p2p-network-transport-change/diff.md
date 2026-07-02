# The change

> ILLUSTRATIVE / SYNTHESIZED diff. PR #351 — "feat(transport): new session
> handshake + ordered message apply". Adds a handshake with a fixed magic
> preamble and applies incoming state updates in arrival order.

```diff
--- a/transport/handshake.go
+++ b/transport/handshake.go
@@ -20,6 +20,17 @@ package transport
 
+// Sent as the first bytes of every session, before the TLS-looking wrapper.
+var sessionMagic = []byte{0x4F, 0x56, 0x52, 0x4C, 0x59, 0x01} // "OVRLY\x01"
+
+func writeHandshake(c net.Conn, id PeerID) error {
+    if _, err := c.Write(sessionMagic); err != nil { // constant 6-byte preamble
+        return err
+    }
+    // fixed-size, fixed-order fields follow: version, peer id, static padding
+    return binary.Write(c, binary.BigEndian, handshakeHeader{Ver: 1, Peer: id})
+}

--- a/transport/apply.go
+++ b/transport/apply.go
@@ -44,15 +44,20 @@ func (s *Session) Recv(msg StateUpdate) error {
-    // previously: buffered and reordered by msg.Seq before applying
-    return s.state.ApplyOrdered(msg)
+    // Apply updates in the order they arrive off the wire.
+    s.state.Apply(msg)              // no Seq check; assumes in-order arrival
+    return nil
 }
 
-func (s *Session) onTimeout(msg StateUpdate) error {
-    return s.resendAndAwait(msg)    // idempotent: guarded by msg.Seq downstream
+func (s *Session) onTimeout(msg StateUpdate) error {
+    // Retransmit on timeout. If the original also lands, Apply runs twice.
+    s.state.Apply(msg)              // re-applies; no dedup by Seq
+    return s.resend(msg)
 }
```
