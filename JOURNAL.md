## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation pipeline decides whether a piece of AI-generated feedback is actually backed up by the source context. Its `_is_supported()` function requires at least two overlapping non-stopword tokens between a claim and its context before marking it as supported. This breaks down for short, factual claims like "The candidate knows Python," which may only share one meaningful word with fully supporting context, so they get scored as unsupported even when they're completely accurate. As a result, feedback made up of short but true claims can score 0.0 for faithfulness, which is misleading. A successful fix will lower or adjust this overlap threshold so short, fully-supported claims are correctly recognized, without breaking the checker's ability to catch claims that truly aren't supported. This affects the `rag/evaluator/faithfulness_checker.py` module.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/davidokebg11/pathreview/commit/5e532f6

**Reproduction summary:**
Ran the exact repro snippet from the issue (`FaithfulnessChecker().check('Knows Python. Knows SQL.', [{'text': 'python expert'}, {'text': 'sql expert'}])`) and confirmed it returns 0.0 instead of a fully-supported score. Also ran `python -m pytest tests/unit/test_faithfulness_checker.py -v`: 4 failed, 18 passed. Three failures (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) match the issue exactly and trace back to the hardcoded `>= 2` meaningful-token-overlap threshold in `_is_supported()` (line 88). A 4th failure, `test_none_context_chunk_text`, is a separate, unrelated `TypeError` bug — noted in PLAN.md but out of scope for this fix.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** [not recorded this week]

**Blockers or open questions:**
Still deciding the exact form of the new threshold rule (see Risks & unknowns in PLAN.md) — want to check a couple of existing tests before finalizing in Week 9.

### Check-in 2 (end of week)

**PR link:** https://github.com/davidokebg11/pathreview/pull/1

**Branch:** fix/152-faithfulness-short-claims

**What you built:** Replaced the fixed `>= 2` meaningful-token-overlap
threshold in `_is_supported()` with a scaled rule
(`ceil(len(claim_meaningful_tokens) / 2)`), fixed punctuation-stripping
in tokenization, and changed `check()` to average continuous per-claim
support ratios instead of counting booleans — the last change was
required after discovering the original boolean-count aggregation could
never produce a partial score for single-claim feedback.

**Tests added or updated:** Added `test_single_meaningful_token_claim_supported`
and `test_single_meaningful_token_claim_not_supported` in
`test_faithfulness_checker.py`. All three originally-failing tests
(`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) now pass.

**Self-review confirmation:** [x] make check passes (no new errors from
this change — pre-existing repo-wide lint debt unrelated to this fix)
[x] make test-unit passes (23 passed, 1 pre-existing unrelated failure
documented above)

**Draft PR feedback received from:** none yet — opened as ready for
review due to time constraints; will address any comments promptly

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Not applicable — reviewer feedback is not a feature in Summer 2026
(per course note).

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Diagnosing the actual bug turned out to be harder than fixing it. My Week 8 reproduction correctly identified the symptom (short claims scoring 0.0) and even correctly identified the buggy line, but my PLAN.md's fix — scaling the overlap threshold — didn't actually work for one of the three tests it was supposed to fix. I only found out because I traced through `test_partial_support_returns_middle_score` by hand and realized `check()`'s formula (`supported/len(claims)`) could only ever return 0.0 or 1.0 for single-claim feedback — no threshold change could produce a partial score. The real fix needed changing how `check()` aggregates scores, which my plan explicitly said was out of scope.

**What did you learn about working in a large codebase?**
A written plan is a hypothesis, not a guarantee — even one based on real reproduction work. In my own projects I'd just start coding and adjust as I go; here, I'd already committed to a specific, documented fix boundary in PLAN.md, and discovering that boundary was wrong mid-implementation meant updating documentation, not just code. I also learned that "passing tests" isn't the same as "correct diagnosis" — three tests were failing for what looked like the same reason, but one of them was failing for a structurally different reason than the other two.

**How did AI tools help — and where did they fall short?**
AI was most useful for mechanical work — tracing through token sets by hand across multiple test cases, writing the boilerplate for new test functions, and catching a punctuation-in-tokenization bug I hadn't noticed. It fell short at the actual judgment call: whether to expand the fix's scope. That decision — and documenting why — was mine to make, and I don't think an AI tool should be the one deciding that a fix's boundaries were wrong.

**What would you do differently if you started over?**
I'd hand-trace at least one example claim through my proposed fix formula during Week 8 planning, before writing PLAN.md — not just re-run the existing tests. If I had run the numbers on `test_partial_support_returns_middle_score` before committing to a plan, I'd have caught the aggregation problem a week earlier.

**What are you most proud of from this module?**
Catching the plan's flaw myself instead of shipping a fix that passed 2 of 3 target tests and calling it done. It would have been easy to declare victory once `test_partial_support_returns_middle_score` was the only one still failing — but the whole point of writing tests first is that you don't get to be satisfied with "mostly."


