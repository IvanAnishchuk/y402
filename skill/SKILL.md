---
name: y402-pay
description: Pay x402-gated (HTTP 402) endpoints using the local y402 wallet. Use when a fetch returns 402 Payment Required or a resource needs micropayment.
---

# Paying with y402

When an HTTP request returns `402 Payment Required`, pay for it with the local wallet:

```bash
y402 pay --unattended <URL>
```

This signs an EIP-3009 USDC authorization locally (gasless, no facilitator) within
the wallet's safety caps and prints the resource body. If it errors with a policy
refusal, the charge exceeded the configured per-payment or daily cap — report that to
the user rather than retrying. Check funds with `y402 balance`.
