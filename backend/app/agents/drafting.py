import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY, MODEL_NAME
from app.my_services import MY_LINK, MY_NAME, MY_PROOF, MY_SERVICES
from app.schemas import DraftResult


MIN_WORDS = 40
MAX_WORDS = 120
MIN_PROMPT_WORDS = 60
MAX_PROMPT_WORDS = 110
MAX_ATTEMPTS = 3


BANNED_PHRASES = [
    "i hope this email finds you well",
    "i hope this finds you well",
    "touch base",
    "just checking in",
    "game-changing",
    "game changer",
    "revolutionary",
    "cutting-edge",
    "synergy",
    "world-class",
    "best-in-class",
]


SYSTEM_PROMPT = """You write short, honest cold outreach emails for a freelancer.

ABOUT THE SENDER (the ONLY claims you may make about them):
{proof}

SERVICES OFFERED:
{services}

STRICT RULES:

- Write the email BODY only. Do not include a greeting, signature, or subject.
- Write between 60 and 110 words in plain text.
- Do not use bullet points, emojis, brackets, or placeholders.
- The body must contain absolutely no numeric digits from zero through nine.
- Do not introduce quantities, percentages, prices, dates, years, employee
  counts, numbered lists, or numerical comparisons.
- Do not spell out numbers as words to disguise numerical claims.
- Do not invent statistics, company facts, sender facts, past clients,
  budgets, results, or unsupported numerical claims.
- If research contains numbers, do not repeat them in the email body.
- Mention exactly ONE specific gap supported by the supplied research.
- Offer ONE concrete, small idea related to that gap.
- Do not promise results or claim that the company will benefit for certain.
- Avoid flattery, hype words, and buzzwords.
- Sound natural, thoughtful, specific, and concise.
- Do not claim to have investigated anything beyond the supplied research.
- End with one low-pressure question, such as asking whether they would
  like to see a short example.
- Before returning the draft, inspect every sentence for numeric digits.
  Rewrite any sentence containing a digit without its numerical claim.
- The subject must be concise and contain no more than eight words.
- Follow all additional validation feedback below.

{feedback}"""


HUMAN_PROMPT = """Company: {name}

Research:
- What they do: {what_they_do}
- Audience: {audience}
- Gaps: {gaps}

Why this company scored well:
{score_reasoning}

Write a personalized email based only on the supplied research.
Do not invent details about the company."""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ]
)


llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GOOGLE_API_KEY,
    max_retries=2,
)


chain = prompt | llm.with_structured_output(DraftResult)


def find_problems(draft: DraftResult) -> list[str]:
    problems = []

    body = draft.body.strip()
    subject = draft.subject.strip()

    words = len(body.split())

    if words < MIN_WORDS or words > MAX_WORDS:
        problems.append(
            f"The body has {words} words. It must contain between "
            f"{MIN_WORDS} and {MAX_WORDS} words."
        )

    if any(ch in body for ch in "[]{}"):
        problems.append(
            "Remove all brackets and placeholders from the body."
        )

    digits_found = sorted(
        set(ch for ch in body if ch.isdigit())
    )

    if digits_found:
        problems.append(
            "The body contains numeric digits: "
            + ", ".join(digits_found)
            + ". Rewrite the entire body without any digits. "
            "Remove the numerical claim instead of spelling out "
            "the number. Check every sentence."
        )

    lowered = body.lower()

    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            problems.append(
                f'Remove the banned phrase "{phrase}".'
            )

    if not subject:
        problems.append("The subject is empty.")

    if len(subject.split()) > 8:
        problems.append(
            "The subject must contain eight words or fewer."
        )

    if any(ch.isdigit() for ch in subject):
        problems.append(
            "Remove all numeric digits from the subject."
        )

    if any(ch in subject for ch in "[]{}"):
        problems.append(
            "Remove brackets and placeholders from the subject."
        )

    return problems


def remove_digit_sentences(body: str) -> str:
    """
    Remove sentences containing numeric digits.

    This is a safety measure before validation, not a substitute
    for generating a correct email.
    """
    sentences = re.split(
        r"(?<=[.!?])\s+",
        body.strip(),
    )

    safe_sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
        and not any(ch.isdigit() for ch in sentence)
    ]

    return " ".join(safe_sentences).strip()


def run_drafting(
    name: str,
    research: dict,
    score_reasoning: str,
) -> tuple[str, str, DraftResult]:

    gaps = research.get("gaps") or []

    base_inputs = {
        "proof": MY_PROOF,
        "services": MY_SERVICES,
        "name": name,
        "what_they_do": research.get(
            "what_they_do",
            "not stated",
        ),
        "audience": research.get(
            "audience",
            "not stated",
        ),
        "gaps": "; ".join(gaps) if gaps else "none found",
        "score_reasoning": score_reasoning or "not available",
    }

    feedback = (
        "Generate an original, personalized email. "
        "Do not include numeric digits in the body or subject."
    )

    last_problems: list[str] = []

    for attempt in range(MAX_ATTEMPTS):
        draft = chain.invoke(
            {
                **base_inputs,
                "feedback": feedback,
            }
        )

        original_body = draft.body.strip()
        cleaned_body = remove_digit_sentences(original_body)

        if cleaned_body != original_body:
            draft = draft.model_copy(
                update={"body": cleaned_body}
            )

        last_problems = find_problems(draft)

        if not last_problems:
            full_body = (
                f"Hi {name} team,\n\n"
                f"{draft.body.strip()}\n\n"
                f"Best,\n"
                f"{MY_NAME}\n"
                f"{MY_LINK.strip()}"
            )

            return (
                draft.subject.strip(),
                full_body,
                draft,
            )

        feedback = (
            "YOUR PREVIOUS DRAFT FAILED VALIDATION.\n"
            "Generate a fresh, complete email body and subject.\n"
            "Correct every problem listed below.\n"
            "Do not repeat the rejected wording.\n"
            "Never include numeric digits in the body or subject.\n"
            "Do not spell numerical claims out as words.\n"
            "Remove unsupported numerical claims completely.\n"
            "Keep the body within the required word limit.\n"
            "Problems:\n"
            + "\n".join(last_problems)
        )

    raise ValueError(
        "Draft failed validation after "
        f"{MAX_ATTEMPTS} attempts: "
        + " ".join(last_problems)
    )

