## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported — https://github.com/ascherj/pathreview/issues/152

### Understand
The root cause is in `_is_supported()` (rag/evaluator/faithfulness_checker.py, line 88). A claim is only marked as "supported" if at least 2 non-stopword tokens overlap between the claim and the context. Short claims like "Knows Python." tokenize to `{"knows", "python"}`, and against context like "python expert" the meaningful overlap is just `{"python"}` — only 1 token. Since 1 is not >= 2, the claim is marked unsupported even though it's fully backed by the context. Expected: short, fully-supported claims should score as supported. Actual: they always score 0.0.

### Map
Files I expect to touch:
- `rag/evaluator/faithfulness_checker.py` — the `_is_supported()` static method, specifically the hardcoded `>= 2` threshold on line 88
- `tests/unit/test_faithfulness_checker.py` — three existing tests already cover this behavior (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`); I may add a new test targeting single-meaningful-token claims specifically

### Plan
1. Replace the fixed `len(meaningful_overlap) >= 2` threshold with a rule that scales down for short claims — e.g. require `len(meaningful_overlap) >= min(2, len(claim_meaningful_tokens))`, so a claim with only 1 meaningful token only needs 1 overlapping token, while longer claims still need at least 2.
2. Re-run `python -m pytest tests/unit/test_faithfulness_checker.py -v` and confirm the three currently-failing tests pass.
3. Add a new unit test for a single-meaningful-token claim (e.g. "Knows Python.") that IS supported, to lock in the fix.
4. Add a new unit test for a single-meaningful-token claim that is NOT supported, to confirm the fix isn't overly lenient.
5. Run `make check` to confirm linting/formatting/type-checking still passes.

### Inputs & outputs
**Input:** a `claim` string and a `context` string, already lowercased/tokenized inside `_is_supported()`.
**Output:** a boolean — True if the claim is considered supported, False otherwise. The fix only changes the threshold logic inside `_is_supported()`, not the function signature or how `check()` aggregates results into the overall float score.

### Risks & unknowns
- Lowering the threshold for short claims could make the checker too lenient, causing short, unsupported claims to be incorrectly marked as supported. I need a test that confirms a short, unsupported claim still returns False.
- Not yet sure whether the "meaningful token count" for the threshold should be based on the claim's token count alone, or the smaller of the claim's and context's meaningful token counts — I'll check `test_common_words_filtered_in_overlap` and `test_minimum_overlap_required` to see what behavior is already locked in by existing tests.
- While reproducing this issue, I also found a separate pre-existing bug (`test_none_context_chunk_text` fails with a `TypeError` when a context chunk's `"text"` key is `None`). This is unrelated to issue #152 and out of scope for this fix, but I want to make sure my change to `_is_supported()` doesn't interact badly with it.

### Edge cases
- Claim with exactly one meaningful token, fully supported by context → should now return True
- Claim with exactly one meaningful token, NOT supported by context → should still return False
- Claim made up entirely of stopwords (zero meaningful tokens) → need to confirm/preserve existing expected behavior
- Long claims with high raw token overlap but low proportional overlap → confirm they aren't over-relaxed by the new rule
- Context chunk with `None` as the text value → known separate bug, should not be introduced or worsened by this change