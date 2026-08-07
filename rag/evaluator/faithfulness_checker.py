"""Check if generated feedback is supported by retrieved context."""

import math
import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0 (ratio of supported claims)
        """
        if not feedback or not context_chunks:
            logger.info(
                "faithfulness_empty_input",
                has_feedback=bool(feedback),
                has_chunks=bool(context_chunks),
            )
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text
        context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])

        # Score each claim on a continuous 0.0-1.0 scale and average,
        # so partially-supported claims contribute partial credit
        ratios = [self._claim_support_ratio(claim, context_text) for claim in claims]
        score = sum(ratios) / len(ratios) if ratios else 0.0

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of claims (sentences)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into lowercase words, stripping punctuation."""
        return set(re.findall(r"\w+", text.lower()))

    @staticmethod
    def _meaningful_tokens(text: str) -> set[str]:
        """Tokenize and remove stop words."""
        stop_words = {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "and",
            "or",
            "but",
            "in",
            "of",
            "to",
            "for",
            "that",
        }
        return FaithfulnessChecker._tokenize(text) - stop_words

    @staticmethod
    def _required_overlap(claim_meaningful_tokens: set[str]) -> int:
        """Overlap needed scales with claim length: at least half the
        claim's meaningful tokens (rounded up), so short claims only
        need 1-2 overlapping tokens instead of a fixed threshold."""
        return math.ceil(len(claim_meaningful_tokens) / 2)

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        claim_tokens = FaithfulnessChecker._tokenize(claim)
        context_tokens = FaithfulnessChecker._tokenize(context)

        overlap = claim_tokens & context_tokens
        claim_meaningful_tokens = FaithfulnessChecker._meaningful_tokens(claim)
        meaningful_overlap = claim_meaningful_tokens & overlap

        if not claim_meaningful_tokens:
            return False

        required_overlap = FaithfulnessChecker._required_overlap(claim_meaningful_tokens)
        return len(meaningful_overlap) >= required_overlap

    @staticmethod
    def _claim_support_ratio(claim: str, context: str) -> float:
        """Compute a continuous 0.0-1.0 support ratio for a claim, so
        partially-supported claims contribute partial credit instead of
        an all-or-nothing boolean.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            Support ratio between 0.0 and 1.0
        """
        claim_tokens = FaithfulnessChecker._tokenize(claim)
        context_tokens = FaithfulnessChecker._tokenize(context)

        overlap = claim_tokens & context_tokens
        claim_meaningful_tokens = FaithfulnessChecker._meaningful_tokens(claim)
        meaningful_overlap = claim_meaningful_tokens & overlap

        if not claim_meaningful_tokens:
            return 0.0

        required_overlap = FaithfulnessChecker._required_overlap(claim_meaningful_tokens)
        return min(1.0, len(meaningful_overlap) / required_overlap)
