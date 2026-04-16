# WebSocket Fanout Simplification

## Objective
Reduce high-cardinality websocket fanout costs under large concurrent socket counts.

## Applied
- Removed per-socket Redis consumer-group lifecycle in websocket gateway.
- Switched to low-cardinality stream read tracking (`xread` with per-connection cursor).
- Kept per-user realtime streams to avoid group churn explosion.

## Next Step (P2+)
- Add shared per-user fanout dispatcher process.
- Optional socket coalescing for multiple tabs/devices.
- Batched delivery/read/typing event aggregation.

