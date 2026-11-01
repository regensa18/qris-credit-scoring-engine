# Technical Decisions

Short, dated records of significant technical decisions and their reasoning to answer the "why"
behind the architecture is discoverable without archaeology through commit history or chat
logs. Each entry follows a lightweight ADR (Architecture Decision Record) shape: context,
decision, consequences.

---

## TD-001: Hexagonal architecture (Ports & Adapters) over layered/Clean Architecture

**Context:** The project has two known, planned swap points: the input format (CSV now, PDF/
screenshot OCR later) and the reasoning engine (simple rule-based now, neurosymbolic/
knowledge-graph reasoning for future development). The architecture needs to make
these swaps cheap.

**Decision:** Use Hexagonal Architecture. The domain layer (`domain/`) defines abstract
interfaces ("ports") for input, validation, feature extraction, reasoning, and output.
Concrete implementations ("adapters") live outside the domain and depend on it, never the
reverse. A single composition root (`main.py`) wires concrete adapters into the pipeline.

**Consequences:** Swapping the reasoning engine means writing a new adapter that implements
`ReasoningPort` and changing one line in the composition root, not touching the pipeline,
domain models, or any other adapter. Full Clean Architecture's additional concentric layers
(entities/use-cases/interface-adapters/frameworks) were deliberately not adopted since the
project's actual swap points don't justify that many layers, and adding them would be
unjustified ceremony for a PoC of this size.

---

## TD-002: Python over Go

**Context:** The author's day job is backend engineering (context not specified as Go, but
common in Indonesian fintech); the question was which language to write this platform in.

**Decision:** Python.

**Reasoning:** The project's own stated end goal is to swap the rule-based reasoning engine
for a neurosymbolic AI engine over a knowledge graph, post-master's. That ecosystem
(`rdflib`/`owlready2` for knowledge graphs, `PyTorch Geometric`/`DGL` for graph learning,
`networkx` for graph manipulation) is overwhelmingly Python-native, with no comparable Go
equivalent. Writing the PoC in Go now would mean the planned reasoning-engine swap becomes a
full platform rewrite rather than a plug-in, defeating the purpose of TD-001's architecture.
Secondary factors: the companion synthetic-data-generator sub-project is already Python
(pandas/numpy), and Python's PDF/OCR ecosystem (for the planned future input format) is
richer than Go's.

**Consequences:** Accepting Python's weaker raw performance and concurrency story versus Go is acceptable, since this is a research PoC, not a high-throughput production payment system.

---

## TD-003: Feature Extraction and Rule Engine are separate pipeline stages

**Context:** It would be simpler to combine "compute signals from transactions" and "judge
those signals" into a single stage.

**Decision:** Keep them strictly separate. Feature Extraction produces only descriptive,
non-judgmental facts (e.g. `revenue_cv: 0.12`); the Rule Engine consumes those facts and
produces judgments (pass/fail, score contribution, explanation).

**Reasoning:** This is what makes the reasoning-engine swap (TD-002) real rather than
aspirational. If judgment logic leaked into Feature Extraction, a future neurosymbolic engine
would need the same facts recomputed in a compatible way, effectively rebuilding this layer
too. Keeping it purely descriptive means the future engine can consume identical input to
today's rule engine.

**Consequences:** Slightly more code/indirection than a combined stage would need. Judged
worth it given the swap is a stated project goal, not a hypothetical.

---

## TD-004: Validation failures produce `null` score + `not_assessed`, never a low numeric score

**Context:** A merchant with insufficient transaction history or a data-integrity red flag
could either (a) be given a low score reflecting "high risk," or (b) be excluded from scoring
entirely with a null score and explanation.

**Decision:** (b). `score: null`, `decision: "not_assessed"`, with a specific explanation of
what failed validation and why.

**Reasoning:** A merchant who was never actually assessed is not the same as one assessed and
found risky, collapsing them into the same numeric scale misrepresents what the engine did.
This is also more consistent with POJK 29/2024 Pasal 2's "tidak menyesatkan" (not misleading)
principle: implying a risk judgment was made when none occurred would be misleading, even if
unintentionally.

**Consequences:** Downstream consumers (e.g. a future API or loan-officer UI) must handle four
outcomes: `eligible`, `manual_review`, `not_eligible` and `not_assessed`, instead of a simple
pass/fail. This is a deliberate, disclosed complexity.

---

## TD-005: Rule weights are hand-assigned constants in external config, not learned parameters

**Context:** "Weights" in a rule-based system and "weights" in a machine learning model are
different concepts that share a name; it would be easy to over-engineer this PoC by importing
ML-style weight-tuning machinery (e.g. optimizing weights against a loss function) where none
is needed.

**Decision:** Weights are simple, hand-assigned point contributions (e.g. `+20`/`-20`) per
rule, justified by one-line domain reasoning each, stored in `config.json`. No fitting,
training, or optimization procedure is applied to them.

**Reasoning:** This PoC's rule engine is deliberately the *simple, swappable* half of the
architecture (see TD-001, TD-003). The sophistication is meant to arrive later via the
neurosymbolic engine, not be smuggled into this stage via ML-style weight learning that would
blur the "simple baseline vs. sophisticated future engine" distinction the project is built
around.

**Consequences:** Weights and rule limits are set from domain reasoning (what a lender would
tolerate), each with a one-line justification. They are not fitted to the fixtures. The
synthetic fixtures and their `expected_eligible` labels are a sanity check on behaviour only;
tuning thresholds to those labels would be circular. The thresholds are therefore not validated
against real repayment outcomes, which is listed as a limitation in the README.

---

## TD-006: Single external config file (JSON) for all tunable values

**Context:** Rule weights, score thresholds, and validation minimums could live scattered
across code, in multiple config files, or in one place.

**Decision:** One `config.json` file holds validation minimums, score thresholds
(including the eligible/review/reject bands), and per-rule weights/enabled flags.

**Reasoning:** For a PoC-stage project, "what's configurable" should be answerable by opening
one file, not by searching the codebase. JSON was chosen over YAML for readability preference;
comment-like documentation is included via `_note`/`_comment` keys since standard JSON has no
native comment syntax.

**Decision:** One `config.json` file holds validation minimums, score thresholds (the
eligible/review bands), and per-rule weights and limits. A rule is active if and only if it has
a block under `rules`; removing the block disables it, and an unknown rule name fails at
startup.

---

## TD-007: Functional Core, Imperative Shell

**Context:** Rules and scoring need to be easy to test and easy to replace.

**Decision:** Feature extraction, rules, scoring and the decision are pure functions of plain
data (`Features`, lists of `RuleResult`, config dicts). Only adapters at the edges do I/O:
reading CSV, writing JSON, loading config. `assess_merchant` only sequences them.

**Reasoning:** Each rule is tested with a hand-built `Features` object and no files. Results
are deterministic, and a new reasoning engine can reuse the same scoring and decision code.

**Consequences:** Data crosses stage boundaries as dataclasses, which adds some boilerplate.

## TD-008: Fair treatment of temporary shocks

**Context:** A temporary closure (fire, renovation, illness) distorts whole-series statistics.
In a simulation, one shock with partial recovery doubled the residual CV of an otherwise flat
merchant (0.072 to 0.141) and made the trend read about -77% over a year. Naive scoring would
punish the same event in several rules.

**Decision:**
1. A shock is 5 or more consecutive zero-sales days, with at least 80% active days in the 14
   days on each side.
2. Stability and trend are measured within the segments between shocks, so the closure and
   the level shift are not read as instability or decline.
3. The shock is judged once, by `shock_recovery`: the ratio of average daily sales in the 28
   days after versus before (the worst ratio across shocks) must be at least 0.8, with at most
   2 shocks per observation window.
4. A rule that does not apply (no shock) is marked `applicable=False` and drops out of that
   merchant's maximum score.
5. The gap rule ignores recognised shock days and regular weekly closure days.

**Reasoning:** Merchants with and without a shock should be judged on equal ground. The ratio
0.8 comes from lender reasoning: a permanent 20% revenue loss can consume most of a small
warung's profit margin. A cap of 2 allows one holiday closure plus one accident.

**Consequences:** Shock-detection parameters (5 days, 14-day window, 80%) are defaults in the
extractor, not in `config.json`. A Lebaran closure looks identical to an accident, since there
is no holiday calendar. A permanently closed business has no recovery window, so it is handled
separately (TD-011). Pooling slopes across segments can shift the measured trend of a strongly
growing merchant (one simulation moved 89.6% to 100.4%), which was not decision-changing.

---

## TD-009: Score aggregation and Bahasa Indonesia explanations

**Decision:** Each applicable rule contributes between -w and +w. The score is
`scale_max * (sum of contributions + M) / (2M)`, where M is the sum of maximum points of the
applicable rules, clamped to 0 to `scale_max`. Each rule returns its own explanation in Bahasa
Indonesia, including the measured value and the limit, from a dedicated messages module.

**Reasoning:** POJK 29/2024 Pasal 32 requires an explanation in Bahasa Indonesia. The earlier
formula floored a raw total of 0 to a score of 0, which was too harsh. Normalising by the
applicable maximum is what makes shocked and unshocked merchants comparable.

**Consequences:** Adding or removing a weighted rule changes how much each other rule counts.
Thresholds must be re-examined whenever the rule set changes. This is why TD-010's blocker has
no weight.

---

## TD-010: Decision policy and approval blockers

**Decision:** `eligible` at a score of 80 or more, `manual_review` from 50 to 79, `not_eligible`
below 50. A weightless rule with `blocks_approval` caps an `eligible` decision at
`manual_review` when it fails.

**Reasoning:** With the current weights (20, 15, 15, 10), a score of 80 or more means no
stability, trend or gap rule failed. A failed recovery alone (-10, giving 83) is tolerated. An
earlier config value of 70 let a merchant with a single failed 15-point rule be auto-approved
(the declining and event-based fixtures), which contradicts the intended policy. The blocker is
separate from the score because "is the business still trading" is a different question from
"how did it behave while trading".

**Consequences:** Score and decision can legitimately differ (a score of 100 with
`manual_review`). Document this in the README.

---

## TD-011: Explicit assessment date (`as_of`)

**Context:** A business that stopped trading leaves no dip to detect; the data just ends.

**Decision:** The use case takes an `as_of` date. The CLI defaults to today. The library
default (`None`) means the last transaction date, so historic fixtures are not flagged merely
for being old. `days_since_last_transaction` feeds the `recent_activity` rule (limit 14 days).

**Consequences:** Tests of the ended-business case must pass `as_of` explicitly. A future API
caller who omits it loses this protection, so the API should require the date or default to
today.

---

## TD-012: Input errors become `not_assessed`

**Decision:** Input adapters raise `InvalidInputError` with a Bahasa Indonesia reason (empty
file, missing columns, an invalid value with its line number, more than one merchant).
`assess_merchant` converts it to `not_assessed` for merchant `UNKNOWN`. A missing file still
raises, as an operator error.

**Reasoning:** This extends TD-004. A malformed file is not a risk judgment, so it never
produces a score.

**Consequences:** User-facing reason strings live in the adapters.