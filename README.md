# Agentic Fuzzing of Mini-XML (mxml)

This repository contains a blackbox, grammar-based fuzzer for
[Mini-XML](https://github.com/michaelrsweet/mxml).

**Target:** mxml `v4.0.4` at commit
`0d5afc4278d7a336d554602b951c2979c3f8f296` (2025-01-19).

## Project summary

I started with an XML grammar and used an LLM to write a
[Hypothesis](https://hypothesis.readthedocs.io/) strategy. Each iteration ran
500 generated documents through a sanitizer build of mxml. The result summary
was then used to revise the strategy. The submitted run stopped after five
iterations and stayed within the $5 budget.

The agentic loop did not use code coverage. Its feedback came from values that
were visible outside the parser: acceptance rate, parser diagnostics, grammar
constructs found in the generated documents, nesting depth, input size, and
execution time.

## Results

The historical campaigns contain 10,000 documents from 19 generated strategies
and one random-text baseline. They found no memory-safety crash and no timeout.

The work did find other problems. A Unicode code point could truncate an mxml
error message or make it invalid UTF-8. I reported this in
[PR #357](https://github.com/michaelrsweet/mxml/pull/357). The maintainer fixed
it in commit `d986100`. The campaign also reproduced a memory leak on the
`<a a>` error path. That leak matches upstream issue
[#354](https://github.com/michaelrsweet/mxml/issues/354).

I used a separate gcov build after the campaigns to compare the saved
strategies. That coverage was never shown to the LLM. Each strategy was run at
seeds 11, 22, and 33, with 500 documents per seed. The random-text baseline
averaged 13.2% parser coverage, although its standard deviation was large at
4.7 points. The first grammar-based strategies averaged 38.7% to 44.9%.

Later iterations helped a little in the three longer runs. Run A gained 0.84
coverage points and the submitted run C gained 1.24. Exploratory run F gained
1.60 points, but it cost $5.45 and is not part of the budget-compliant result.
In runs A and C, iteration 2 performed better than the final strategy.

Distinct parser diagnostics were the most useful feedback signal. Their
correlation with corrected coverage was at least +0.83 in each longer run.
Production counts were much weaker because most strategies already generated
nearly all 27 tracked constructs.

## Main files

- `docs/REPORT.md`: the two-page report.
- `docs/comparison.md`: coverage method, run comparison, and limitations.
- `docs/findings.md`: defects, crash triage, and remaining gaps.
- `docs/design-decisions.md`: engineering choices and their reasons.
- `grammar/ADAPTATIONS.md`: differences between the ANTLR grammar and mxml.
- `runs/loop-c/ITERATION_LOG.md`: the submitted run, iteration by iteration.

The submitted run is `runs/loop-c`. It used five iterations and six LLM calls,
including one repair call. Its recorded cost was $4.51.

## Repository layout

| path | contents |
|---|---|
| `grammar/` | ANTLR XML grammar and tested adaptations |
| `harness/` | C driver, sanitizer build, and smoke tests |
| `fuzzer/` | campaign runner, measurements, and crash triage |
| `agent/` | agentic loop, prompts, validation, and LLM backends |
| `runs/` | corpora, strategies, summaries, and transcripts |
| `docs/` | report and supporting analysis |

## Running the checks

```bash
./run.sh build
./run.sh shell
./scripts/verify_replay.sh loop-c
```

Outside Docker:

```bash
./scripts/fetch_target.sh
python3 -m virtualenv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m fuzzer.selftest   # 101 assertions
./harness/smoke_test.sh               # 20 assertions
```

## Reproducibility

Every campaign stores the exact bytes sent to the harness in
`corpus.jsonl.gz`. Replay uses those bytes and checks the saved classifications
and corpus digest. All 2,500 inputs in each five-iteration run replay with the
same classifications.

The LLM itself is not deterministic. Every prompt and response is therefore
saved under `runs/<id>/transcript/`. Transcript replay reconstructs the saved
strategy files byte for byte. It does not make a new LLM generation.

The serializer was corrected after the historical campaigns. Because of that,
the original corpora remain historical evidence, while the corrected coverage
study reruns the saved strategy code with fixed seeds. The old measurements are
kept under `runs/analysis/pre-serializer-fix/`. Current strategy measurements
are in `runs/analysis/coverage_trials.json`, and the matching random-text
baseline is in `runs/analysis/baseline_coverage_trials.json`.

`fuzzer/strategies/byte_probe.py` is a fixed eight-input check for rare byte
cases, including UTF-16 byte-order marks, truncated UTF-16, malformed UTF-8, an
embedded NUL, and a contradictory encoding declaration. Its saved run is
`runs/byte-probe`.

## Configuration

Backend settings and secrets are read from `.env`. That file is ignored by Git
and is not included in the repository.

```bash
cp .env.example .env
```

| `LLM_BACKEND` | requirement | purpose |
|---|---|---|
| `replay` | none | replay the saved transcript without network access |
| `openai` | `OPENAI_API_KEY`, `OPENAI_BASE_URL` | use an OpenAI-compatible endpoint |
| `cli` | `CLAUDE_CODE_OAUTH_TOKEN` | use Claude Code headless |
