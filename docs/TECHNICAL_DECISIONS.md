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

**Consequences:** Requires downstream consumers (e.g. a future API or loan-officer UI) to
handle a three-state outcome (scored-eligible, scored-ineligible, not-assessed) rather than a
simple pass/fail, a deliberate disclosed complexity.

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

**Consequences:** Weight values are tuned empirically by hand (generate synthetic merchants →
check the engine's output against known `expected_eligible` ground truth → adjust) rather than
via any statistical procedure. This is intentional and matches the same empirical-tuning
discipline used throughout the companion synthetic-data-generator sub-project.

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

**Consequences:** As the project grows, a single flat-ish config file may need restructuring
(e.g. per-environment configs). Acceptable to defer until that need is concrete, per the same
"don't build for hypothetical future scope" discipline applied elsewhere in this project.