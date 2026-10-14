from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY, MODEL_NAME
from app.my_services import IDEAL_CLIENT, MY_SERVICES
from app.schemas import ScoreResult


SYSTEM_PROMPT = """You are a strict lead-qualification analyst working for a freelancer.

Your job is to identify companies that are genuinely suitable for the
freelancer's services, not merely companies that have problems.

FREELANCER SERVICES:
{services}

IDEAL CLIENT:
{ideal_client}

SCORING RUBRIC — TOTAL 100 POINTS:

1. Industry fit: 0-35 points
   How closely does the company's business match the ideal client?

2. Visible need: 0-35 points
   Does the provided research identify specific, credible problems that
   the freelancer's services could realistically help address?

3. Reachability: 0-20 points
   How realistic is it for a freelancer to reach and work with this company?
   Consider company size, complexity, and the likely accessibility of
   decision-makers.

   Suggested guidance:
   - Small businesses and small startups: generally score higher.
   - Small and medium-sized companies: assess individually.
   - Companies with hundreds of employees: apply a substantial penalty
     unless the research supports a realistic opportunity.
   - Very large multinational enterprises: generally score low because
     they are less accessible to an individual freelancer.

4. Evidence quality: 0-10 points
   How specific and reliable is the provided research?

DECISION GUIDANCE:

- 0-49: Generally skip.
- 50-69: Borderline. Assess fit, reachability, and evidence carefully.
- 70-80: Strong potential lead, requiring credible evidence.
- Above 80: Rare. Requires strong evidence across the categories.

STRICT RULES:

- Base your assessment ONLY on the supplied research.
- Never invent company facts, employee counts, budgets, or hiring plans.
- A company's existence or industry alone does not establish that it is
  a good prospect.
- Do not award a high score merely because the company has several gaps.
- Distinguish a genuine opportunity from a problem that the freelancer
  is unlikely to be able to address.
- Large company size must meaningfully reduce reachability when the
  research provides evidence that the company is difficult to approach.
- Do not automatically reject every medium-sized company.
- Add the four scoring categories to calculate the total.
- Keep the reasoning to 2-3 sentences and mention specific research details.
- Return a structured result matching the requested schema."""


HUMAN_PROMPT = """Company: {name}

Research:
- What they do: {what_they_do}
- Audience: {audience}
- Gaps: {gaps}
- Research confidence: {confidence}

Assess whether this company is a realistic prospect for the freelancer.
Pay particular attention to company size, industry fit, and the specificity
of the identified gaps."""


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

chain = prompt | llm.with_structured_output(ScoreResult)


def run_scoring(name: str, research: dict) -> ScoreResult:
    gaps = research.get("gaps") or []

    return chain.invoke(
        {
            "services": MY_SERVICES,
            "ideal_client": IDEAL_CLIENT,
            "name": name,
            "what_they_do": research.get("what_they_do", "not stated"),
            "audience": research.get("audience", "not stated"),
            "gaps": "; ".join(gaps) if gaps else "none found",
            "confidence": research.get("confidence", "low"),
        }
    )