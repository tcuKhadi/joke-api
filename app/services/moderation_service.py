"""Content moderation: profanity, quality, duplication, and LLM self-check."""

from better_profanity import profanity
from rapidfuzz import fuzz

from app.services.llm_service import llm_service

profanity.load_censor_words()

MIN_LENGTH = 10
MAX_LENGTH = 500
DUPLICATE_THRESHOLD = 90

SELF_CHECK_PROMPT = (
    "Is the following text an appropriate, coherent joke with no hate "
    "speech, slurs, or harmful content? Respond with only YES or NO.\n\n"
    "Text: {content}"
)


class ModerationService:
    """Runs generated content through layered moderation checks."""

    def check_length(self, content: str) -> bool:
        """Reject content that is too short or too long to be a real joke."""
        length = len(content.strip())
        return MIN_LENGTH <= length <= MAX_LENGTH

    def check_profanity(self, content: str) -> bool:
        """Return True if content passes (contains no profanity)."""
        return not profanity.contains_profanity(content)

    def check_duplicate(self, content: str, existing: list[str]) -> bool:
        """Return True if content passes (no near-duplicate found)."""
        for existing_content in existing:
            score = fuzz.ratio(content.lower(), existing_content.lower())
            if score >= DUPLICATE_THRESHOLD:
                return False
        return True

    def check_llm_self_review(self, content: str) -> bool:
        """Ask the local model to judge its own output as a final check."""
        prompt = SELF_CHECK_PROMPT.format(content=content)
        result = llm_service.generate(prompt, temperature=0.1, max_tokens=5)
        verdict = result["text"].strip().upper()
        return verdict.startswith("YES")

    def moderate(self, content: str, existing: list[str]) -> bool:
        """Run all checks; return True only if content passes every stage."""
        if not self.check_length(content):
            return False
        if not self.check_profanity(content):
            return False
        if not self.check_duplicate(content, existing):
            return False
        if not self.check_llm_self_review(content):
            return False
        return True


moderation_service = ModerationService()