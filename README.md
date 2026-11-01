# QRIS Credit Scoring Engine

A rule-based, explainable credit eligibility engine for Indonesian MSMEs. It reads a merchant's
QRIS transaction history from a CSV file and returns a score from 0 to 100, a decision, and a
per-rule explanation in Bahasa Indonesia.

This is a proof of concept (phase one). It runs on **synthetic data only**; no real merchant
data is used or included. It is not a production lending product.

## Why this exists

Many Indonesian MSMEs have no credit bureau history, so conventional scoring cannot assess them.
They do generate a continuous record of business health through QRIS payments. This project
tests whether that record alone can support a transparent, auditable eligibility assessment,
following the transparency principles of POJK 29/2024 (explanations in Bahasa Indonesia, a
documented methodology, no use of credit-bureau data).

The rule engine is deliberately the simple, replaceable half of the design. The architecture
(see below) lets a more sophisticated reasoning engine, such as a neurosymbolic one over a
knowledge graph, replace it without touching the rest of the pipeline.

## Quick start

Requires Python 3.10 or newer (developed on 3.14).

```bash
git clone <this repository>
cd qris-credit-scoring-engine

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python main.py tests/fixtures/SYN-seasonal-fried_chicken_stall-UMI-6.csv --as-of 2025-12-31
```

Run the tests:

```bash
python -m pytest
```

## Usage

```bash
python main.py <path-to-merchant-csv> [--as-of YYYY-MM-DD]
```

- `<path-to-merchant-csv>`: one CSV file for **one merchant**.
- `--as-of`: the assessment date. It defaults to today. The engine uses it to notice a merchant
  who has stopped trading: a business that closes for good leaves no dip in the data, because
  the data simply ends. When you assess historical or synthetic files, pass the last day of the
  period you want to assess, otherwise old files will look as if they stopped long ago.

The result is printed as JSON.

### Input format

| Column | Required | Notes |
|---|---|---|
| `merchant_id` | yes | A single value in the whole file |
| `date` | yes | `YYYY-MM-DD` |
| `amount` | yes | A number greater than 0 |
| `rrn` | recommended | Transaction reference, used to detect duplicates |
| `type`, `mcc`, `business_type`, `merchant_business_scale` | optional | Read if present |

Extra columns are ignored.

A file that cannot be assessed (empty, missing a required column, a bad value, more than one
merchant, too little history) does not crash the engine and does not receive a score. It returns
`not_assessed` with a specific reason.

### Output

```json
{
  "merchant_id": "SYN-seasonal-fried_chicken_stall-UMI-6",
  "engine": "rule_based_v1",
  "score": 100,
  "decision": "eligible",
  "approval_blocked_by": [],
  "explanations": [
    {
      "rule": "revenue_stability",
      "applicable": true,
      "passed": true,
      "points": 20,
      "explanation": "Pendapatan harian stabil: fluktuasi di luar pola tren dan hari dalam seminggu sekitar 13% (batas 25%)."
    },
    {
      "rule": "trend_direction",
      "applicable": true,
      "passed": true,
      "points": 15,
      "explanation": "Tren pendapatan stabil atau naik: perubahan sekitar -1.0% per bulan (batas penurunan 5% per bulan)."
    },
    {
      "rule": "shock_recovery",
      "applicable": false,
      "passed": true,
      "points": 0,
      "explanation": "Tidak ada penutupan sementara yang terdeteksi; penilaian pemulihan usaha tidak diterapkan."
    },
    {
      "rule": "structural_irregularity_handling",
      "applicable": true,
      "passed": true,
      "points": 15,
      "explanation": "Kontinuitas usaha baik: hari tanpa penjualan yang tidak terjelaskan 0% (batas 10%), jeda terpanjang 0 hari (batas 7 hari)."
    },
    {
      "rule": "recent_activity",
      "applicable": true,
      "passed": true,
      "points": 0,
      "explanation": "Usaha masih aktif: transaksi terakhir 0 hari yang lalu (batas 14 hari)."
    }
  ]
}
```

A file that cannot be assessed returns, for example:

```json
{
  "merchant_id": "...",
  "engine": "rule_based_v1",
  "score": null,
  "decision": "not_assessed",
  "reason": "Jumlah transaksi tidak mencukupi untuk dilakukan penilaian. Ditemukan 5 transaksi, minimum yang dibutuhkan adalah 30 transaksi."
}
```

A `not_assessed` merchant is deliberately not given a low score. A merchant who was never
assessed is not the same as one assessed and found risky.

## Decisions

| Decision | Meaning |
|---|---|
| `eligible` | Score of 80 or more, and no approval blocker triggered |
| `manual_review` | Score from 50 to 79, or an eligible score held back by a blocker |
| `not_eligible` | Score below 50 |
| `not_assessed` | The input could not be assessed; no score is given |

With the default weights, a score of 80 or more means no stability, trend or gap rule failed. A
failed recovery alone is tolerated.

The score describes how the merchant behaved while trading. A blocker (`approval_blocked_by`)
describes whether the merchant is still trading. They are separate questions, so a score of 100
with `manual_review` is possible and intended.

## The rules

| Rule | What it checks | Default limit | Points |
|---|---|---|---|
| `revenue_stability` | Day-to-day swing in sales, after removing the trend and the weekday pattern | at most 25% | +20 / -20 |
| `trend_direction` | Change in sales per month. Growth earns no bonus | decline of at most 5% per month | +15 / -15 |
| `structural_irregularity_handling` | Days with no sales that are not explained by a recognised closure or a regular weekly day off | at most 10% of days; longest stretch at most 7 days | +15 / -15 |
| `shock_recovery` | After a temporary closure, whether sales returned to their earlier level | at least 80% of the earlier level; at most 2 closures | +10 / -10 |
| `recent_activity` | Days since the last transaction, measured to the assessment date | at most 14 days | no points; blocks automatic approval |

**Fair treatment of temporary closures.** A closure of 5 or more days (fire, renovation,
illness) is excluded from the stability and trend measurements and judged once, by
`shock_recovery`. If a merchant has no such closure, `shock_recovery` is marked not applicable
and removed from that merchant's maximum score, so merchants with and without a shock are
compared on equal ground. The reasoning is in `docs/TECHNICAL_DECISIONS.md` (TD-008).

## Configuration

Every weight, limit and threshold lives in one file, `config.json`. A rule is active if it has a
block under `rules`; remove the block to disable it.

```json
"rules": {
  "revenue_stability": { "weight_if_passed": 20, "weight_if_failed": -20, "max_residual_cv": 0.25 },
  "trend_direction": { "weight_if_passed": 15, "weight_if_failed": -15, "min_monthly_change": -0.05 },
  "shock_recovery": { "weight_if_passed": 10, "weight_if_failed": -10,
                      "min_recovery_ratio": 0.8, "max_excusable_shocks": 2 },
  "structural_irregularity_handling": { "weight_if_passed": 15, "weight_if_failed": -15,
                      "max_unexplained_gap_share": 0.10, "max_unexplained_longest_gap_days": 7 },
  "recent_activity": { "max_days_without_sales": 14 }
},
"scoring": { "scale_max": 100, "eligible_threshold": 80, "review_threshold": 50 }
```

Weights are simple hand-assigned numbers justified by domain reasoning. They are not learned
from data (see TD-005).

## How it is built

The pipeline has five stages: input, validation, feature extraction, reasoning, and output.

```
CSV  ->  Input  ->  Validation  ->  Feature extraction  ->  Rule engine  ->  Score + decision  ->  JSON
```

It uses Hexagonal Architecture (ports and adapters). The domain defines the interfaces; the
concrete parts, such as the CSV reader, the validator, the statistical feature extractor and the
JSON writer, are adapters that implement them. `main.py` is the only place that wires concrete
classes together. Feature extraction only describes the data; the rule engine alone judges it.
That separation is what makes the reasoning engine replaceable.

```
domain/        models, ports (interfaces), scoring, the assess use case, errors
adapters/
  input/       CSV reader
  validation/  basic validator
  features/    statistical feature extractor
  reasoning/   rule engine, one file per rule, Bahasa Indonesia messages
  output/      JSON writer
config/        config loader
docs/          PRD and technical decisions
tests/         unit tests, end-to-end tests and synthetic fixtures
main.py        composition root and command-line interface
```

More detail: [`docs/PRD.md`](docs/PRD.md) and [`docs/TECHNICAL_DECISIONS.md`](docs/TECHNICAL_DECISIONS.md).

## Test data

All test data is synthetic, produced by the companion project
`qris_synthetic_data_generation`, which generates QRIS-style transactions for several merchant
archetypes (steady, growing, declining, volatile, seasonal, event-based) with optional temporary
closures. The fixtures in `tests/fixtures/` come from that generator. They contain no real
merchants, transactions or proprietary schemas.

## Limitations

- Thresholds and weights come from domain reasoning and are not validated against real
  repayment outcomes. Agreement with the generator's `expected_eligible` label is a sanity check
  of behaviour, not a measure of accuracy.
- Event-based merchants (for example bazaar vendors) are not assessed on their own terms. They
  pass stability and trend, which look only at days with sales, and are caught by the gap rule
  alone, which sends them to manual review.
- A holiday closure (such as Lebaran) looks the same as any other closure.
- `recent_activity` is a simple 14-day check, and the closure-detection parameters are defaults
  in the code, not in the config.
- One merchant per file. The merchant profile is currently a placeholder and no rule uses it.
- CSV input only.

## Roadmap

Planned for later phases: persistent storage of results, an HTTP API, CI, Docker, additional
input formats (Excel, PDF), and a neurosymbolic reasoning engine as a replacement for the rule
engine.

## Disclaimer

This is a research and portfolio project. It is not a licensed credit scoring product and makes
no claim of compliance with POJK 29/2024; it adopts that regulation's transparency principles as
design targets.