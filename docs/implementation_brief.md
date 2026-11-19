# Implementation Brief: Should This Use AI?

## 1. Your Workflow

My dad manages six machines in Manizales, Colombia. Six operators send handwritten records or photos of hour-meter readings. He organizes them in notebooks and Excel to review maintenance needs. He estimates spending eight hours per week on recordkeeping and related work. My baseline log records a 23-minute call about the records; a complete maintenance review remains unmeasured.

The completed Pasto IGAC pilot contains one snapshot, 500 parcels, and 1,218 building records. With my approval, Codex checked the record relationships, repeat loading, audit timestamps, five SQL queries, database permissions, and local validation in a new Python environment. Collecting maintenance data in Manizales and building the dashboard, chatbot, and agent are still planned. [Technical design](schema.md) · [Baseline](baseline_log.md)

## 2. Should This Use AI?

| Option | Benefits | Costs and risks |
|---|---|---|
| A. Existing tools | Improve the Excel template and review checklist. | Low cash cost; manual effort and mistakes remain. |
| B. Data and SQL | Structured records and a dashboard could support traceable maintenance reviews. | Setup, training, accurate readings, and confirmed intervals are needed. |
| C. LLM chatbot | Could answer questions about records in natural language. | API costs, privacy exposure, and incorrect answers require testing. |

I recommend Option B. I would add an LLM only if testing shows value beyond ordinary reports. My dad will approve maintenance decisions.

## 3. Value Hypothesis

My target is a 50% reduction in the median time needed to review all six machines, without reducing accuracy. I have not measured the baseline or achieved an improvement yet. I will time three complete reviews using the current process and three comparable reviews after implementing Option B. I will record them in the Milestone 4 usage log and compare the median, or middle, times. My dad will check results against meter readings, service records, and confirmed intervals. We will record corrections. These six reviews provide an initial comparison; assessing lasting improvement requires more observations.

## 4. Early Cost Estimate

| Service | Proposed monthly cost and assumption |
|---|---|
| Supabase | $0, Free plan within database and traffic limits. |
| GitHub Actions | $0, daily sync using standard runners in the public repository. |
| Render | $0, one Free website within included usage. |
| GPT-5.4 mini, optional | $3.75 for 1,000 calls, averaging 2,000 input and 500 billed output tokens. |

Pricing checked November 18, 2026 gives API rates of $0.75 per million input tokens and $4.50 per million output tokens. Estimated monthly costs are $0 for Option B, plus $3.75 for optional AI: $1.50 for input and $2.25 for output. This excludes taxes, setup and training time, paid upgrades, and extra API features. Free-service limits, sleep, or suspension could interrupt access.

I propose an initial $20 prepaid allowance with auto-reload disabled. Additional purchases require my approval. Before paid AI use, I will implement and test a control that reserves each request’s maximum cost, including retries, and blocks requests that could exceed the remaining allowance. Prepaid billing may not stop charges immediately. When the limit is reached, AI requests will stop. Ordinary reports will remain available while hosting is operational. [Supabase](https://supabase.com/pricing) · [Actions](https://docs.github.com/en/actions/concepts/billing-and-usage) · [Render](https://render.com/docs/free) · [API rates](https://developers.openai.com/api/docs/models/gpt-5.4-mini) · [Prepaid limits](https://help.openai.com/en/articles/8264644-setting-up-and-managing-prepaid-api-billing)

## 5. Risks and Governance

Incorrect readings could affect my dad, operators, customers, and people near machines. My dad approves maintenance decisions and record changes. I manage pilot access and spending. I plan to provide a way for operators to report errors. Private machinery, worker, and customer records stay separate from public IGAC data. Private business records will not be published on the public website. Public visitors must not see private records or receive unverified maintenance advice. AI must never independently change records, mark services complete, or make safety-critical decisions. Unreliable information requires human review. Manizales map coverage and IGAC reuse terms remain unresolved.

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

For Freshness and Monitoring, I plan to test scheduled IGAC sync and failure logging, then separately develop checks for missing machinery readings. For Measured Value and Cost, I will compare logged review times, track expenses, and test the spending limit before paid AI use.
