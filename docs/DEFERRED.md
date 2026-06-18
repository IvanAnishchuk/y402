# Deferred findings / tech debt

Accepted-as-is findings surfaced during subagent-driven implementation of the
v1 plan. None are correctness bugs; each was reviewed and consciously deferred.
Revisit before a 1.0 / mainnet-enable milestone.

| ID | Module | Finding | Severity | Decision |
|----|--------|---------|----------|----------|
| DEF-1 | `money.py` | `from_atomic` is typed `int` but has no runtime guard, so a stray `float` would be accepted silently. Internal callers always pass `int`/atomic values. | Minor | Accept for v1; add an `isinstance` guard only if an external caller appears. |
| DEF-2 | `registry.py` | `REGISTRY` is a plain mutable `dict`; nothing prevents runtime reassignment of entries. Could wrap in `types.MappingProxyType`. No call site mutates it. | Minor | Accept for v1; wrap if registry integrity becomes a concern. |

| DEF-3 | `x402_client.py` | `select_offer` branch coverage: the "cheapest fallback when no default-network match" branch can't be exercised with v1's single enabled network; the "non-exact scheme is skipped" branch is also untested. | Minor | Add targeted tests in Task 16 (or when a 2nd network is enabled). |
| DEF-4 | `x402_client.py` | We emit/consume the x402 **V1** envelope (`x402Version: 1`); output validates against `x402.schemas.v1.PaymentPayloadV1`. The installed x402 2.13.0 also ships a newer `PaymentPayload` (with an `accepted` field) for a later protocol version. | Minor | Accept V1 for v1. Revisit if sellers/facilitators require the newer envelope. |

| DEF-5 | `x402_client.py` `select_offer` | Offers were filtered by `scheme=="exact"` + enabled registry network, but `offer.asset` was NOT checked against `network.usdc_address`. | Low (correctness, no fund-loss) | ✅ **FIXED** — `select_offer` now skips offers whose `asset` ≠ the registry USDC address. |

| DEF-6 | `chain.py` `transfer_usdc` | No explicit `gas`/`maxFeePerGas`; `build_transaction` relies on the node's `eth_estimateGas`/fee oracle. Fine for a reachable RPC; a flaky/limited node would surface a clear error (not silent). | Low | Accept for v1; add explicit gas controls if RPC estimation proves unreliable. |
| DEF-7 | test suite / `pyproject.toml` | web3 transitively imports `websockets.legacy`, emitting a `DeprecationWarning` during tests. Harmless (not our code; currently a warning, not an error). | Trivial | Optionally add a `filterwarnings` ignore in Task 16 to cut noise. |

| DEF-8 | `transfer.py` / `audit.py` | A manual `send` records `decision="pay"`, so `spent_today()` counts it toward the *automated* x402 daily cap (shared "total daily spend" model). | Low (design) | ✅ **DECIDED (#13):** keep the total-daily-wallet-spend model for v1; documented in `audit.spent_today` docstring + CLAUDE.md. Alternative (scope cap to `kind=="x402"`) left to the maintainer if an agent-only allowance is preferred. |

| DEF-9 | `cli.py` | `Decimal(amount)` in `send`/`config set` and `enabled_networks()[0]` in `send` were unguarded (raw `InvalidOperation`/`IndexError` tracebacks). | Low (UX, fail-safe) | ✅ **FIXED** — `_usd()` parses with a clean `typer.Exit(1)`; `send` validates recipient (`Web3.is_address`) + positive amount; `send` uses `config.default_network` (no IndexError). (#9) |

## Findings from the final whole-implementation review

| ID | Module | Finding | Severity | Decision |
|----|--------|---------|----------|----------|
| DEF-10 | `x402_client.py` `parse_offers`/`policy.evaluate` | Seller-controlled `maxAmountRequired` was `int()`-parsed with no lower bound: a **negative** amount → PAY, an audited negative `"pay"` **reduced** `spent_today` (daily-cap erosion), then `sign_typed_data` crashed with `ValueOutOfBounds`. | **Important (security)** | ✅ **FIXED** — `select_offer` skips `max_amount_atomic <= 0`; `policy.evaluate` refuses `amount <= 0` (defense-in-depth). |
| DEF-11 | `keystore.py` `save_key` | `write_text(...)` then `chmod(0o600)` left a brief world-readable (`0o644`) window; the write was also non-atomic (torn keystore possible on crash). | Important | ✅ **FIXED** — atomic `mkstemp` (0o600 from creation) + `Path.replace`; no window, no torn file. |
| DEF-12 | `audit.py` `read_all` | A single corrupt/torn JSONL line made `read_all` raise, breaking `spent_today` (the cap check) and `y402 log`. | Minor | ✅ **FIXED** — `read_all` skips + `logger.warning`s unparseable lines (#6). |
| DEF-13 | `audit.py` / `transfer.py` | `AuditRecord.host` means a hostname for x402 but a recipient **address** for `send`. Cosmetic, but conflates the field for any analysis. | Trivial | Document the overload or add a distinct field. |
| DEF-14 | `chain.py` / spec | `transfer_usdc` returns right after `send_raw_transaction`; the send is audited before any receipt, so a later-reverting tx is still logged `"pay"`. Spec's send flow said "await receipt". | Low | Accept for v1 (hash is real); revisit with receipt-await if needed. |
| DEF-3-domain | `x402_client.py` `build_payment` | EIP-712 domain `name`/`version` fell back to seller-supplied `offer.domain_name/version`. | Minor | ✅ **FIXED** — domain `name`/`version` now pinned to the registry (`select_offer` guarantees the asset matches). |

## Findings from `/code-review high`

Fixed in this pass (with tests): ✅ httpx.Client now closed when pay() owns it;
✅ select_offer rejects implausible `maxTimeoutSeconds` (`0 < t <= 3600`) so a
hostile seller can't mint a years-long authorization; ✅ malformed 402 bodies
raise a clean `NoUsableOfferError` instead of a raw traceback (and null
`resource` → `""`); ✅ `send` now defaults to `config.default_network` like
`pay` (also removes the `enabled_networks()[0]` IndexError path).

Deferred:

| ID | Module | Finding | Severity | Decision |
|----|--------|---------|----------|----------|
| DEF-15 | `config.py` / `chain.py` | `Config.rpc_overrides` was declared/persisted/settable but never applied — `ChainClient` always used `network.rpc_url` (a false affordance). | Low | ✅ **DECIDED + FIXED (#12):** wired — `ChainClient(network, rpc_url=...)`; `balance`/`send` pass `config.rpc_overrides.get(net.id)`, falling back to the registry endpoint. |
| DEF-16 | `x402_client.py` / `transfer.py` | Daily-cap check is not atomic: two concurrent CLI invocations both read the same `spent_today` snapshot and can each pass the cap (TOCTOU). Inherent to the file-based ledger. | Low (needs concurrent invocations) | Accept for v1 (CLI is normally sequential); revisit with a lock/lease if parallel automation is expected. |
| DEF-17 | `audit.py` `spent_today` | Re-reads + parses the whole JSONL log on every pay() (O(N) on the hot path). | Low (log is small for micropayments) | Accept for v1; stream/aggregate or roll the log if it grows large. |
| DEF-18 | `x402_client.py` `pay` | Only `GET` is supported for the probe + paid retry; x402-gated `POST`/other-method resources can't be paid without threading a method param through. | Low (v1 scope) | Accept for v1. |
| DEF-19 | `audit.py` / `x402_client.py` / `transfer.py` | `decision` is stored as raw string literals (`"pay"`/`"refuse"`) rather than `Decision` enum values; a rename would silently desync `spent_today`. Plus minor dup (network-resolution block in `balance`/`send`). | Trivial | Cosmetic cleanup; defer. |

`send` intentionally bypasses `policy.evaluate` (caps are for *automated* x402
payments; a manual `send` is an explicit, confirmed user action) — by design,
not a defect. `transfer_usdc` not awaiting a receipt before auditing is DEF-14.

## Plan corrections applied during implementation

- **Canonical test vector (Tasks 8, 10):** the plan paired `KEY = 0x59c6995e…78690d` with `ADDR = 0x7E5F4552…395Bdf`, but those don't correspond. Verified: `0x59c6995e…` → `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` (Hardhat acct #1); `0x7E5F4552…` is the address of key `0x…0001`. Tests use the corrected pair `KEY=0x59c6995e…` / `ADDR=0x70997970C51812dc3A010C7d01b50e0d17dc79C8`. Apply the same correction anywhere the plan reuses this pair.
