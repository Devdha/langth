"""Pydantic schemas for the v2 API.

This module defines all request and response models for the therapy sentence
generation API v2.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Language(str, Enum):
    """Supported languages for therapy sentence generation."""

    KO = "ko"
    EN = "en"


class DiagnosisType(str, Enum):
    """Types of diagnoses supported by the therapy system."""

    SSD = "SSD"  # Speech Sound Disorder
    ASD = "ASD"  # Autism Spectrum Disorder
    LD = "LD"  # Language Delay


class TherapyApproach(str, Enum):
    """Therapy approaches for sentence generation."""

    MINIMAL_PAIRS = "minimal_pairs"
    MAXIMAL_OPPOSITIONS = "maximal_oppositions"
    COMPLEXITY = "complexity"
    CORE_VOCABULARY = "core_vocabulary"


ALLOWED_APPROACHES_BY_DIAGNOSIS: dict["DiagnosisType", set["TherapyApproach"]] = {
    DiagnosisType.SSD: {
        TherapyApproach.MINIMAL_PAIRS,
        TherapyApproach.MAXIMAL_OPPOSITIONS,
        TherapyApproach.COMPLEXITY,
    },
    DiagnosisType.ASD: {TherapyApproach.CORE_VOCABULARY},
    DiagnosisType.LD: {TherapyApproach.CORE_VOCABULARY},
}


class CommunicativeFunction(str, Enum):
    """Communicative functions for therapy sentences."""

    REQUEST = "request"
    REJECT = "reject"
    HELP = "help"
    CHOICE = "choice"
    ATTENTION = "attention"
    QUESTION = "question"


class PhonemePosition(str, Enum):
    """Positions where a phoneme can occur in a syllable."""

    ONSET = "onset"
    NUCLEUS = "nucleus"
    CODA = "coda"
    ANY = "any"


class DifficultyLevel(str, Enum):
    """Difficulty levels for therapy sentences."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PhonologicalRulesMode(str, Enum):
    """Modes for handling phonological rules in sentence generation.

    Attributes:
        AVOID: Avoid sentences that trigger phonological rules.
        ALLOW: Allow sentences with phonological rules naturally.
        TRAIN: Specifically target sentences for phonological rule training.
    """

    AVOID = "avoid"
    ALLOW = "allow"
    TRAIN = "train"


class TargetConfig(BaseModel):
    """Configuration for target phoneme in therapy sentences.

    Attributes:
        phoneme: The target phoneme to practice (1-3 characters).
        position: The position of the phoneme in the syllable.
        minOccurrences: Minimum number of times the phoneme should appear.
    """

    phoneme: str = Field(..., min_length=1, max_length=3)
    position: PhonemePosition
    minOccurrences: int = Field(default=1, ge=1, le=3)


class GenerateRequestV2(BaseModel):
    """Request model for generating therapy sentences.

    Attributes:
        language: The language for sentence generation (ko or en).
        age: Target age group (3-7 years).
        count: Number of sentences to generate (1-20).
        target: Configuration for the target phoneme (optional for core_vocabulary).
        sentenceLength: Number of words in each sentence (2-6).
        diagnosis: The diagnosis type for therapy customization.
        therapyApproach: The therapy approach to use.
        theme: Optional theme for sentence content.
        communicativeFunction: Optional communicative function to target.
        core_words: Optional list of core vocabulary words to include.
        phonological_rules_mode: Optional mode for handling phonological rules.
    """

    language: Language
    age: Literal[3, 4, 5, 6, 7]
    count: int = Field(..., ge=1, le=20)
    target: TargetConfig | None = None  # Optional for core_vocabulary approach
    sentenceLength: int = Field(..., ge=2, le=6)
    diagnosis: DiagnosisType
    therapyApproach: TherapyApproach
    theme: str | None = None
    communicativeFunction: CommunicativeFunction | None = None
    core_words: list[str] | None = None
    phonological_rules_mode: PhonologicalRulesMode | None = None

    @model_validator(mode="after")
    def _validate_approach_constraints(self) -> "GenerateRequestV2":
        allowed = ALLOWED_APPROACHES_BY_DIAGNOSIS.get(self.diagnosis, set())
        if allowed and self.therapyApproach not in allowed:
            allowed_values = ", ".join(a.value for a in sorted(allowed, key=lambda a: a.value))
            raise ValueError(
                f"therapyApproach '{self.therapyApproach.value}' is not allowed for diagnosis "
                f"'{self.diagnosis.value}'. Allowed: {allowed_values}"
            )

        if self.therapyApproach != TherapyApproach.CORE_VOCABULARY and self.target is None:
            raise ValueError("target is required for non-core_vocabulary therapyApproach")

        return self


class MatchedWord(BaseModel):
    """A word that matches the target phoneme criteria.

    Attributes:
        word: The matched word.
        startIndex: Starting character index in the sentence.
        endIndex: Ending character index in the sentence.
        positions: List of positions where the phoneme occurs.
    """

    word: str
    startIndex: int
    endIndex: int
    positions: list[PhonemePosition]


class TherapyItemV2(BaseModel):
    """A generated therapy sentence with metadata.

    Attributes:
        id: Unique identifier for the sentence.
        text: The generated sentence text.
        target: The target phoneme configuration used (optional for core_vocabulary).
        matchedWords: Words in the sentence that contain the target phoneme.
        wordCount: Number of words in the sentence.
        score: Quality score for the sentence.
        difficulty: Optional difficulty level for the sentence.
        tokens: Optional tokenized sentence.
        diagnosis: The diagnosis type used for generation.
        approach: The therapy approach used.
        theme: Optional theme used for generation.
        function: Optional communicative function targeted.
    """

    id: str
    text: str
    target: TargetConfig | None = None  # Optional for core_vocabulary approach
    matchedWords: list[MatchedWord]
    wordCount: int
    score: float
    difficulty: DifficultyLevel | None = None
    tokens: list[str] | None = None
    diagnosis: DiagnosisType
    approach: TherapyApproach
    theme: str | None = None
    function: CommunicativeFunction | None = None


class TokenizedSentence(BaseModel):
    """A sentence with tokenization information.

    Attributes:
        text: The original sentence text.
        tokens: List of tokens (words/morphemes) in the sentence.
    """

    text: str
    tokens: list[str]


class ContrastSet(BaseModel):
    """A pair of sentences for contrast-based therapy.

    Attributes:
        targetWord: The word containing the target phoneme.
        contrastWord: The word containing the contrasting phoneme.
        targetSentence: The sentence with the target phoneme.
        contrastSentence: The sentence with the contrasting phoneme.
    """

    targetWord: str
    contrastWord: str
    targetSentence: TokenizedSentence
    contrastSentence: TokenizedSentence


class GenerateMetaV2(BaseModel):
    """Metadata about the generation response.

    Attributes:
        requestedCount: Number of sentences requested.
        generatedCount: Number of sentences actually generated.
        averageScore: Average quality score of generated sentences.
        processingTimeMs: Processing time in milliseconds.
    """

    requestedCount: int
    generatedCount: int
    averageScore: float
    processingTimeMs: int


class GenerateDataV2(BaseModel):
    """Data payload for generation responses.

    Attributes:
        items: Generated therapy items (for sentence-based approaches).
        contrastSets: Generated contrast sets (for minimal_pairs/maximal_oppositions).
        meta: Metadata about generation.
    """

    items: list[TherapyItemV2] | None = None
    contrastSets: list[ContrastSet] | None = None
    meta: GenerateMetaV2


class GenerateResponseV2(BaseModel):
    """Successful response model for sentence generation.

    Attributes:
        success: Always True for successful responses.
        data: Dictionary containing items, contrastSets, and meta.
    """

    success: Literal[True]
    data: GenerateDataV2


class ErrorCode(str, Enum):
    """Error codes for API error responses."""

    INVALID_REQUEST = "INVALID_REQUEST"
    GENERATION_FAILED = "GENERATION_FAILED"
    INSUFFICIENT_RESULTS = "INSUFFICIENT_RESULTS"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    """Detailed error information.

    Attributes:
        code: The error code.
        message: Human-readable error message.
        details: Optional additional details about the error.
    """

    code: ErrorCode
    message: str
    details: str | None = None


class ErrorResponseV2(BaseModel):
    """Error response model for API errors.

    Attributes:
        success: Always False for error responses.
        error: Detailed error information.
    """

    success: Literal[False]
    error: ErrorDetail


class ScriptFadingResult(BaseModel):
    """Result of script fading for therapy progression.

    Attributes:
        full_script: The complete sentence/script.
        fade_steps: Progressive fading steps from full to minimal cues.
    """

    full_script: str
    fade_steps: list[str]
