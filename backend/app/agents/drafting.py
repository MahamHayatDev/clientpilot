from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY, MODEL_NAME
from app.my_services import MY_LINK, MY_NAME, MY_PROOF, MY_SERVICES
from app.schemas import DraftResult

MIN_WORDS = 40
MAX_WORDS = 120
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
- Write the email BODY only. No greeting, no signature, no subject inside the body.
- 60 to 110 words. Plain text. No bullet points, no emojis, no brackets or placeholders.
- Mention exactly ONE specific gap from the research, in a neutral and respectful way.
  Never say their product or work is bad.
- Offer ONE concrete, small idea related to that gap. Do not promise results.
- Never invent facts about the company, the sender, past clients, or numbers.
- No flattery, hype words, or buzzwords. Sound like a thoughtful person, not a template.
- End with one low-pressure question, for example asking if they would like a short example.
{feedback}"""

HUMAN_PROMPT = """Company: {name}

Research:
- What they do: {what_they_do}
- Audience: {audience}
- Gaps: {gaps}

Why this company scored well: {score_reasoning}"""

prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
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
    words = len(body.split())

    if words < MIN_WORDS or words > MAX_WORDS:
        problems.append(
            f"The body has {words} words. It must be between 60 and 110 words."
        )
    if any(ch in body for ch in "[]{}"):
        problems.append("Remove all brackets and placeholders.")
    lowered = body.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            problems.append(f'Remove the phrase "{phrase}".')
    if len(draft.subject.split()) > 10:
        problems.append("The subject must be 8 words or fewer.")
    if not draft.subject.strip():
        problems.append("The subject is empty.")
    return problems


def run_drafting(
    name: str, research: dict, score_reasoning: str
) -> tuple[str, str, DraftResult]:
    gaps = research.get("gaps") or []
    base_inputs = {
        "proof": MY_PROOF,
        "services": MY_SERVICES,
        "name": name,
        "what_they_do": research.get("what_they_do", "not stated"),
        "audience": research.get("audience", "not stated"),
        "gaps": "; ".join(gaps) if gaps else "none found",
        "score_reasoning": score_reasoning or "not available",
    }

    feedback = ""
    last_problems: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        draft = chain.invoke({**base_inputs, "feedback": feedback})
        last_problems = find_problems(draft)
        if not last_problems:
            full_body = (
                f"Hi {name} team,\n\n{draft.body.strip()}\n\n"
                f"Best,\n{MY_NAME}\n{MY_LINK}"
            )
            return draft.subject.strip(), full_body, draft
        feedback = "\nYOUR PREVIOUS ATTEMPT WAS REJECTED. Fix these problems: " + " ".join(
            last_problems
        )

    raise ValueError("Draft failed validation: " + " ".join(last_problems))