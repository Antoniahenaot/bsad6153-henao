# Implementation Brief: Should This Use AI?

*Working draft for review. Assignment 4.3 AI-use permission is unconfirmed.*

## 1. Your Workflow

My dad manages six machines in Manizales, Colombia. Six operators send handwritten records or hour-meter photos. He organizes them in notebooks and Excel to review maintenance needs. He estimates eight hours weekly for recordkeeping and related work. My baseline log records a 23-minute explanatory call, but complete maintenance-review time remains unmeasured.

The completed Pasto IGAC pilot has one snapshot, 500 parcels, and 1,218 building records. After my approval, Codex verified relationships, repeat loading, audit timestamps, five SQL queries, restricted roles, and fresh-environment local validation. Manizales maintenance collection, dashboard, chatbot, and agent features remain planned. [Technical design](schema.md) · [Baseline](baseline_log.md)

## 2. Should This Use AI?

| Option | Benefits | Costs and risks |
|---|---|---|
| A. Existing tools | Improve the Excel template and review checklist. | Low cash cost; manual effort and mistakes remain. |
| B. Data and SQL | Structured records and a dashboard could support traceable maintenance reviews. | Setup, training, accurate readings, and confirmed intervals are needed. |
| C. LLM chatbot | Could answer questions about records in natural language. | API costs, privacy exposure, and incorrect answers require testing. |

I recommend Option B. Add an LLM only if testing demonstrates additional value beyond ordinary reports. Maintenance decisions require human approval.

## 3. Value Hypothesis

I propose reducing median review time for all six machines by 50% without reducing accuracy. No measured baseline or improvement exists yet. I will time three complete reviews using the current process and three comparable reviews after Option B, recording times in the Milestone 4 usage log. My dad will verify results against meter readings, service records, and confirmed intervals. We will record corrections alongside times. Six observations provide an initial pilot comparison; lasting improvement needs further observation.

## 4. Early Cost Estimate

| Service | Proposed monthly cost and assumption |
|---|---|
| Supabase | $0, Free plan within database and traffic limits. |
| GitHub Actions | $0, daily sync using standard runners in the public repository. |
| Render | $0, one Free website within included usage. |
| GPT-5.4 mini, optional | $3.75 for 1,000 calls, averaging 2,000 input and 500 billed output tokens. |

Verified November 18, 2026: API rates are $0.75/million input and $4.50/million output tokens, giving $1.50 + $2.25 = $3.75. Option B's listed services total an estimated $0/month; optional AI raises that to $3.75. These are estimates, excluding taxes, setup/training time, paid upgrades, and extra API features. Free-service limits, sleep, or suspension can affect availability.

I propose an initial $20 prepaid allowance, auto-reload disabled, and approval before additional purchases. Before paid AI use, an application control must reserve each request's maximum cost, including retries, and block requests exceeding the remaining allowance. It must be implemented and tested. Prepaid billing may not stop charges immediately. At the limit, AI stops; ordinary reports remain available while hosting works. [Supabase](https://supabase.com/pricing) · [Actions](https://docs.github.com/en/actions/concepts/billing-and-usage) · [Render](https://render.com/docs/free) · [API rates](https://developers.openai.com/api/docs/models/gpt-5.4-mini) · [Prepaid limits](https://help.openai.com/en/articles/8264644-setting-up-and-managing-prepaid-api-billing)

## 5. Risks and Governance

Incorrect readings could affect my dad, operators, customers, and people near machines. My dad approves maintenance decisions and record changes. I manage pilot access and spending and plan a way for operators to report errors. Private machinery, worker, and customer records stay separate from public IGAC data. Private business records will not be published on the public website. Public visitors must not see private records or receive unverified maintenance advice. AI must never independently change records, mark services complete, or make safety-critical decisions. Unreliable information requires human review. Manizales map coverage and IGAC reuse terms remain unresolved.

## 6. Scorecard Self-Assessment

| Factor | Rating | Reason |
|---|---|---|
| Real user and workflow | Green | User and workflow identified. |
| Data access | Yellow | IGAC available; business collection pending. |
| Data understanding | Yellow | IGAC documented; maintenance rules unconfirmed. |
| Freshness and monitoring | Red | Sync and monitoring unimplemented. |
| Grounding | Yellow | Traceable SQL; chatbot unimplemented and untested. |
| Bounded autonomy | Yellow | Business approval controls planned. |
| Evaluation | Yellow | Database tested; maintenance accuracy untested. |
| Measured value and cost | Red | Review times and operating costs unmeasured. |
| Adoption | Yellow | Regular use untested. |
| Governance and accountability | Yellow | Roles verified; business controls need testing. |

For Freshness and Monitoring, test scheduled IGAC sync and failure logging; separately develop missing-reading checks for machinery. For Measured Value and Cost, compare logged review times, track expenses, and test the spending stop before paid AI use.
