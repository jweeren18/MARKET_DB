# Schwab Market Data API — Quick Reference

Source: Schwab Developer API v1.0.0 (`https://api.schwabapi.com/marketdata/v1`)

---

## Quotes

### Bulk — `GET /quotes`
Fetch quotes for multiple symbols in a single request.

| Param | Type | Required | Notes |
|---|---|---|---|
| `symbols` | string | yes | Comma-separated list. Supports equities, ETFs, options, futures, forex, indices |
| `fields` | string | no | Subset filter: `quote`, `fundamental`, `extended`, `reference`, `regular`. Default: all |
| `indicative` | bool | no | If true, also returns indicative quotes (`$ABC.IV`) for every ETF in the list |

**Response**: `{ "AAPL": { ... }, "MSFT": { ... } }` — keyed by symbol.

**Useful `fundamental` fields returned per symbol:**
`eps`, `peRatio`, `divYield`, `divAmount`, `divFreq`, `avg10DaysVolume`, `avg1YearVolume`,
`declarationDate`, `divExDate`, `divPayDate`, `nextDivExDate`, `nextDivPayDate`

**Max symbols per request**: Not documented. Test empirically — start at 100, binary-search for limit.

### Single — `GET /{symbol_id}/quotes`
Same response shape but one symbol only. Use for interactive/on-demand lookups; prefer bulk for pipeline work.

---

## PriceHistory

### `GET /pricehistory`
**Single symbol only.** No comma-separated list support.

| Param | Type | Required | Notes |
|---|---|---|---|
| `symbol` | string | yes | Single equity symbol |
| `periodType` | string | no | `day`, `month`, `year`, `ytd` |
| `period` | int | no | Number of periods (see valid values below) |
| `frequencyType` | string | no | `minute`, `daily`, `weekly`, `monthly` |
| `frequency` | int | no | Duration unit (see valid values below) |
| `startDate` | int64 | no | Epoch ms. If omitted: `endDate - period` |
| `endDate` | int64 | no | Epoch ms. If omitted: previous market close |
| `needExtendedHoursData` | bool | no | Include pre/post market |
| `needPreviousClose` | bool | no | Include previous close price + date |

### Valid periodType / frequencyType / frequency combos

| periodType | frequencyType | valid frequency values | default period |
|---|---|---|---|
| `day` | `minute` | 1, 5, 10, 15, 30 | 10 |
| `month` | `daily` | 1 | 1 |
| `month` | `weekly` | 1 | 1 |
| `year` | `daily` | 1 | 1 |
| `year` | `weekly` | 1 | 1 |
| `year` | `monthly` | 1 | 1 |
| `ytd` | `daily` | 1 | 1 |
| `ytd` | `weekly` | 1 | 1 |

Valid `period` counts by periodType:
- `day`: 1, 2, 3, 4, 5, 10
- `month`: 1, 2, 3, 6
- `year`: 1, 2, 3, 5, 10, 15, 20
- `ytd`: 1

> **Note:** There is no 60-minute (`1h`) frequency. Finest intraday granularity is 30-minute.
> If `startDate`/`endDate` are provided they override the `period` range.

**Response:**
```json
{
  "symbol": "AAPL",
  "empty": false,
  "previousClose": 174.56,
  "previousCloseDate": 1639029600000,
  "candles": [
    { "open": 175.01, "high": 175.15, "low": 175.01, "close": 175.04, "volume": 10719, "datetime": 1639137600000 }
  ]
}
```
`datetime` is epoch milliseconds.

---

## Other Endpoints (not yet explored in detail)

| Endpoint | Description |
|---|---|
| `GET /instruments` | Search by symbol or description. `projection` param: `symbol-search`, `symbol-regex`, `desc-search`, etc. |
| `GET /movers/{index}` | Top gainers/losers for an index. Potentially useful for opportunity scoring without fetching all symbols. |
| `GET /markets` | Market hours / holiday schedule |
| `GET /optionchains` | Option chain data |
| `GET /optionexpirations` | Option expiration dates |

---

## Rate Limits

| Operation category | Limit |
|---|---|
| Market data (quotes, price history, option chains) | **120 calls / minute** |
| Trading operations | 60 calls / minute |
| Account data | 60 calls / minute |
| Daily order messages | 4,000 / day |

- Limit is **per API key** (i.e., per OAuth credential). Fanning out to multiple pods does NOT increase the quota — all pods share the same 120/min ceiling.
- Exceeding the limit returns **HTTP 429**. Back off at least 60 seconds before retrying.
- For continuous real-time data, use the **streaming WebSocket API** instead of polling REST endpoints.

---

## Scaling Implications

| Stage | Endpoint used | Symbols per call | Calls for 4k tickers | Minutes at 120/min |
|---|---|---|---|---|
| Daily price ingest | `GET /pricehistory` | 1 | **4,000** | **~34 min** |
| Quote refresh | `GET /quotes` | N (bulk) | **~40–100** | <1 min |
| Fundamentals | `GET /quotes?fields=fundamental` | N (bulk) | **~40–100** | <1 min |

### What this means for the pipeline architecture

**Stage 1 (ingest) is rate-limit bound, not CPU bound.** 4,000 sequential calls at 120/min ≈ 34 minutes. That's fine for a once-daily run — no need to fan out this stage across multiple pods. Multiple pods would just race each other to the same 120/min cap and trigger 429s.

**Stages 2–4 (indicators, scoring, alerts) are CPU bound.** They read from the local DB, no Schwab calls. These are the stages that benefit from K8s fan-out.

**Revised pipeline shape:**
```
Stage 1: Ingest        → single pod, built-in rate limiter (sleep 0.5s between calls)
Stage 2: Indicators    → fan-out across N pods (pure computation)
Stage 3: Scoring       → fan-out across N pods (pure computation)
Stage 4: Alerts        → single pod (compares scores, lightweight)
```

A client-side rate limiter (token bucket or simple 0.5s sleep between `/pricehistory` calls) in `data_ingestion.py` keeps us safely under the 120/min limit without needing a shared coordinator.

---

## Known Issues in Our Code

1. **`_FREQUENCY_MAP["1h"]`** in `market_data_service.py` maps to `("minute", "day")` with `frequency=1`.
   That produces 1-minute candles, not 1-hour. Schwab has no 60-min frequency — max intraday is 30 min.
   The pipeline only uses `"1d"` today so this is dormant, but the entry is misleading.

2. **`schwab_client.get_quote()`** calls `GET /quotes/{symbol}` (single-symbol endpoint).
   Should switch to `GET /quotes?symbols=...` (bulk) once we add a `get_quotes_bulk()` method.

---

*Last updated: 2026-02-03*
