## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation pipeline decides whether a piece of AI-generated feedback is actually backed up by the source context. Its `_is_supported()` function requires at least two overlapping non-stopword tokens between a claim and its context before marking it as supported. This breaks down for short, factual claims like "The candidate knows Python," which may only share one meaningful word with fully supporting context, so they get scored as unsupported even when they're completely accurate. As a result, feedback made up of short but true claims can score 0.0 for faithfulness, which is misleading. A successful fix will lower or adjust this overlap threshold so short, fully-supported claims are correctly recognized, without breaking the checker's ability to catch claims that truly aren't supported. This affects the `rag/evaluator/faithfulness_checker.py` module.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger