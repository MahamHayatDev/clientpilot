# ClientPilot evaluation results

Run date: 2026-10-23 | Model: gemini-3.5-flash-lite | Score threshold: 50

Labels were written by the project author. Borderline cases are judgment calls.

## Lead scoring

| Metric | Result |
|---|---|
| Cases attempted | 20 |
| Cases completed | 20 |
| Cases failed | 0 |
| Decision accuracy (completed cases) | 95% |
| Decision accuracy (clear cases) | 100% |
| Decision accuracy (borderline cases) | 75% |
| Precision (contacted leads that were good) | 92% |
| Recall (good leads that were contacted) | 100% |
| Average score, good leads | 69.5 |
| Average score, bad leads | 26.5 |
| Score consistency (average difference) | 3 points |
| Score consistency (maximum difference) | 6 points |

### Average category-score differences on repeat runs

| Category | Average absolute difference |
|---|---:|
| industry_fit | 1.2 points |
| visible_need | 1.2 points |
| reachability | 0.6 points |
| evidence_quality | 0 points |

Failed cases are excluded from scoring metrics.

## Lead-level scoring diagnostics

| Company | Score | Industry /35 | Need /35 | Reachability /20 | Evidence /10 | Decision | Expected | Correct |
|---|---:|---:|---:|---:|---:|---|---|---|
| LedgerLoop | 85 | 32 | 28 | 16 | 9 | contact | contact | True |
| PayNest | 65 | 30 | 15 | 12 | 8 | contact | contact | True |
| TaxPilot AI | 79 | 30 | 25 | 15 | 9 | contact | contact | True |
| BudgetBee | 64 | 30 | 10 | 15 | 9 | contact | contact | True |
| InvoiceFlow | 86 | 33 | 28 | 16 | 9 | contact | contact | True |
| CrediScore Labs | 64 | 30 | 10 | 15 | 9 | contact | contact | True |
| SplitEase | 68 | 30 | 15 | 15 | 8 | contact | contact | True |
| RemitFast | 74 | 30 | 20 | 15 | 9 | contact | contact | True |
| StackBooks | 76 | 30 | 22 | 15 | 9 | contact | contact | True |
| FinLearn Hub | 58 | 20 | 15 | 15 | 8 | contact | contact | True |
| MidBank Digital | 67 | 28 | 20 | 10 | 9 | contact | skip | False |
| HealthTrack SaaS | 61 | 22 | 15 | 16 | 8 | contact | contact | True |
| Khan and Co Accountants | 54 | 15 | 15 | 15 | 9 | contact | contact | True |
| FreshMart Online | 33 | 5 | 10 | 10 | 8 | skip | skip | True |
| Mamas Kitchen | 18 | 0 | 0 | 10 | 8 | skip | skip | True |
| OmniPay Global | 28 | 20 | 0 | 0 | 8 | skip | skip | True |
| Sunrise Yoga Studio | 20 | 2 | 0 | 10 | 8 | skip | skip | True |
| BrightSmile Dental | 18 | 0 | 0 | 10 | 8 | skip | skip | True |
| HardWheels Auto Parts | 28 | 5 | 5 | 10 | 8 | skip | skip | True |
| Unreadable Site | 0 | n/a | n/a | n/a | n/a | skip | skip | True |

### Reasoning and matched services

#### LedgerLoop

- Reasoning: LedgerLoop operates directly in the financial and automation software space, aligning well with the freelancer's fintech and workflow automation capabilities. The documented manual email onboarding process provides a clear, credible operational gap that matches workflow automation services. Furthermore, their small target audience size and high-confidence research suggest they are realistically reachable for a direct freelancer engagement.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph, Fintech workflow automation: document extraction, anomaly flagging, dashboards

#### PayNest

- Reasoning: PayNest operates in the mobile payments and merchant services sector, showing a strong industry fit for fintech workflow automation. However, the identified gaps regarding support options and missing help content only weakly indicate a need for support triage or information workflows without confirmed operational burdens. Direct freelancer reachability is moderately plausible given their small-to-mid startup scope.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### TaxPilot AI

- Reasoning: TaxPilot AI is an AI-driven tax preparation tool for sole proprietors, representing a strong industry alignment. The research notes that document uploads are reviewed manually by staff, creating a credible practical use for document extraction and workflow automation services. Reachability is plausible given the early-stage nature of an AI assistant startup.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### BudgetBee

- Reasoning: BudgetBee operates in the personal finance and SaaS space, providing a strong industry fit. However, the research gaps mainly point to missing developer documentation and content rather than documented backend or workflow automation needs, limiting the visible service need. Given the small startup profile implied by the app focus, direct freelancer reachability is moderately plausible.
- Matched services: Backend and API development: FastAPI services and integrations

#### InvoiceFlow

- Reasoning: InvoiceFlow operates directly in the invoicing and billing space, showing a strong industry fit. Research highlights specific manual late-payment follow-ups, aligning well with communication and workflow automation services. Furthermore, their small-to-medium business focus makes direct freelancer engagement realistic based on the provided high-confidence data.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### CrediScore Labs

- Reasoning: CrediScore Labs operates in the fintech and API sector, creating a strong industry fit for backend development. However, the documented gaps relate solely to developer documentation and missing plain-language resources rather than operational workflows, limiting the direct need for automation or custom services. Reachability is moderately plausible for an early-stage API provider, and the high-confidence research clearly supports the company's profile.
- Matched services: Backend and API development: FastAPI services and integrations

#### SplitEase

- Reasoning: SplitEase operates in the payments and expense-splitting space, giving it a strong industry fit for the freelancer's fintech workflow and automation services. However, the visible need is limited to handling support through a single shared inbox, which moderately supports support triage automation. Direct reachability is reasonably plausible given the early-stage nature of an expense-splitting app for students and travelers.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph (support triage)

#### RemitFast

- Reasoning: RemitFast operates in the payments and remittance sector, creating a strong alignment for workflow and automation services. The research notes manual identity verification steps in their FAQ, offering a plausible opportunity for document extraction or backend integration. Direct freelancer reachability is moderately plausible given their startup nature, backed by high-confidence research.
- Matched services: Fintech workflow automation: document extraction, anomaly flagging, dashboards., AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### StackBooks

- Reasoning: StackBooks provides SaaS bookkeeping software to digital agencies, creating a strong industry and service alignment. The manual receipt capture gap creates a practical opening for document extraction and workflow automation. As a small software company targeting modest-sized agencies, direct freelancer reachability is plausible based on the available research evidence.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph, Fintech workflow automation: document extraction, anomaly flagging, dashboards

#### FinLearn Hub

- Reasoning: FinLearn Hub operates in personal finance education with a relevant business model, though it is not a pure SaaS or fintech firm. The research indicates a lack of automated email sequences and searchable course categories, pointing to potential workflow or backend optimization needs. However, these gaps represent general website improvements rather than confirmed technical automation demands.
- Matched services: AI automation, Backend and API development

#### MidBank Digital

- Reasoning: MidBank Digital operates in retail banking with around 800 employees, showing a relevant business model for fintech-related workflows. The research identifies manual document steps in loan applications, creating a plausible opportunity for document extraction and workflow automation, though its larger size introduces moderate reachability barriers for an individual freelancer.
- Matched services: Fintech workflow automation: document extraction, anomaly flagging, dashboards, AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### HealthTrack SaaS

- Reasoning: HealthTrack SaaS operates a B2B software model with a relevant use case for communication automation in onboarding and reminders. The research identifies manual phone-based onboarding and a lack of appointment reminders as plausible operational gaps, though the evidence is limited to high-level observations. Given the small target size of independent clinics, the company is approachable for an individual freelancer.
- Matched services: AI automation: building workflows and agents with n8n, LangChain and LangGraph

#### Khan and Co Accountants

- Reasoning: Khan and Co Accountants is a local accounting firm with an indirect connection to fintech workflows. The research indicates manual document collection via email and a lack of an online invoicing portal, creating a moderate opportunity for document extraction or workflow automation. As a small local business, direct access is plausible, though their operational scale limits the urgency and budget for custom technical solutions.
- Matched services: Fintech workflow automation: document extraction, anomaly flagging, dashboards., AI automation: building workflows and agents with n8n, LangChain and LangGraph (invoice processing, lead research, support triage, reporting, approval flows).

#### FreshMart Online

- Reasoning: FreshMart Online is a regional grocery chain operating outside the freelancer's core fintech or SaaS focus. Although they have a manual order confirmation process, the evidence is too limited to establish a credible technical service match beyond general web development. Therefore, the company is not a realistic prospect and should be skipped.
- Matched services: None identified

#### Mamas Kitchen

- Reasoning: Mamas Kitchen is a local family restaurant operating completely outside the freelancer's target domains of fintech, SaaS, or AI automation. The research shows a lack of online ordering, but this is a standard e-commerce or point-of-sale requirement rather than a need for AI workflows, FastAPI services, or fintech engineering.
- Matched services: None identified

#### OmniPay Global

- Reasoning: OmniPay Global operates in the payments industry, but its massive size of approximately 40,000 employees and reliance on large in-house teams make it entirely unsuitable for an individual freelancer. The research confirms there are no visible operational gaps or opportunities for external automation services.
- Matched services: None identified

#### Sunrise Yoga Studio

- Reasoning: Sunrise Yoga Studio is a local neighborhood yoga business with no connection to fintech, SaaS, or AI automation. The research notes gaps like image-based schedules and lack of online booking, but these require standard web development rather than the freelancer's specialized AI, backend, or workflow automation services.
- Matched services: None identified

#### BrightSmile Dental

- Reasoning: BrightSmile Dental is a local dental clinic with no connection to fintech, SaaS, or AI-adjacent operations. The research notes that appointment requests are by phone only, which does not present a credible technical service match for the freelancer's offerings. Therefore, this company is not a realistic prospect.
- Matched services: None identified

#### HardWheels Auto Parts

- Reasoning: HardWheels Auto Parts operates as an automotive brake parts manufacturer rather than a fintech, payments, SaaS, or AI-adjacent company. While their downloadable PDF catalog indicates manual ordering processes, this does not establish a clear need for the freelancer's specific automation, backend, or fintech services. Consequently, the company is not a realistic prospect and falls below the contact threshold.
- Matched services: None identified

#### Unreadable Site

- Reasoning: Research confidence is low; lead skipped.
- Matched services: None identified

## Repeat-run consistency details

### LedgerLoop

- Total score: 85 -> 88
- Absolute total-score difference: 3
- industry_fit: 32 -> 35 (difference: 3)
- visible_need: 28 -> 28 (difference: 0)
- reachability: 16 -> 16 (difference: 0)
- evidence_quality: 9 -> 9 (difference: 0)

### PayNest

- Total score: 65 -> 68
- Absolute total-score difference: 3
- industry_fit: 30 -> 30 (difference: 0)
- visible_need: 15 -> 15 (difference: 0)
- reachability: 12 -> 15 (difference: 3)
- evidence_quality: 8 -> 8 (difference: 0)

### TaxPilot AI

- Total score: 79 -> 82
- Absolute total-score difference: 3
- industry_fit: 30 -> 30 (difference: 0)
- visible_need: 25 -> 28 (difference: 3)
- reachability: 15 -> 15 (difference: 0)
- evidence_quality: 9 -> 9 (difference: 0)

### BudgetBee

- Total score: 64 -> 64
- Absolute total-score difference: 0
- industry_fit: 30 -> 30 (difference: 0)
- visible_need: 10 -> 10 (difference: 0)
- reachability: 15 -> 15 (difference: 0)
- evidence_quality: 9 -> 9 (difference: 0)

### InvoiceFlow

- Total score: 86 -> 80
- Absolute total-score difference: 6
- industry_fit: 33 -> 30 (difference: 3)
- visible_need: 28 -> 25 (difference: 3)
- reachability: 16 -> 16 (difference: 0)
- evidence_quality: 9 -> 9 (difference: 0)

## Outreach drafting

| Metric | Result |
|---|---|
| Drafts attempted | 8 |
| Drafts completed | 8 |
| Draft-generation failures | 0 |
| Passed quality checks | 100% |
| Average body length | 66 words |

Quality checks flag unsupported numbers, banned phrases, and gaps that do not match the research.
