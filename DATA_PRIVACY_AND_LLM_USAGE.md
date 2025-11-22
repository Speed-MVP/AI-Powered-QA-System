Data Privacy, Confidentiality & LLM Usage Requirements

This document defines how the system must handle audio, transcripts, metadata, and evaluation information when interacting with LLMs. These rules are mandatory for confidentiality, legal compliance, BPO standards, and data protection regulations (GDPR/CCPA/law-of-contracts).

1. PII Redaction Before LLM

The system must NEVER send raw personally identifiable information to the LLM.

Redact the following before passing transcript text to the model:

Customer name

Agent name

Phone numbers

Email addresses

Physical addresses

Birthdays

Account numbers (bank, customer ID, CRM ID)

Credit card numbers

Order numbers

Government IDs

Any unique identifying codes

Replace with placeholders:

{{NAME}}

{{PHONE}}

{{EMAIL}}

{{ACCOUNT_NUMBER}}

{{CARD_NUMBER}}

{{ADDRESS}}

2. Prompt Minimization

Only send the minimum transcript content required for LLM scoring.

For each stage evaluation, send ONLY:

Transcript segments for that stage

Deterministic step results for that stage

Rule violations relevant to that stage

Stage definition from FlowVersion

Rubric mapping for that stage

Never send:

Full call transcript

Previous stage transcripts

Audio file

Agent real names

Customer real names

Company identity

Internal URLs

Backend IDs

Full policy documents

3. Zero Data Retention Configuration

All LLM calls must use no-training / zero-data-retention mode.

Must ensure:

Provider does NOT store prompts

Provider does NOT store outputs

Provider does NOT use data for model training

Provider does NOT use data for analytics

This setting must be explicitly enabled for every API call.

4. Do Not Store Raw Prompts

The system must not save:

Full LLM request body

Raw transcript sent to LLM

Any sensitive prompt content

Only store:

LLM output

Redacted transcript

Evaluation results

Deterministic evidence

Raw prompt logging must be disabled.

5. Data Encryption (Mandatory)

All data involved in evaluation must be encrypted:

In Transit

HTTPS / TLS 1.2+

No plain HTTP allowed

At Rest

Cloud bucket encryption (AES-256)

Database encryption (AES-256)

6. Identity Masking

Do NOT send:

Agent name → replace with Agent

Customer name → replace with Customer

Company name → never included

Branding → not included

Internal departments → not included

Keep the evaluation model context-free.

7. No Unnecessary Metadata

Do NOT pass these to the LLM:

recording_id

flow_version_id

company_id

user_id

timestamps of upload

file path / cloud bucket URL

IPs

geographic location

Only internal services should handle these — NOT the LLM.

8. Transcript Sanitization

Before sending text to LLM:

Remove profanity markers

Remove CRM URL references

Remove system messages

Remove back-end logs

Only the actual dialogue + redacted placeholders should remain.

9. Stage-Based Transcript Separation

LLM must only receive the transcript segments for the stage being evaluated.

Example:

Opening stage → only greeting + verification lines

Discovery stage → probing questions related lines

Resolution stage → solution lines

Closing stage → wrap-up lines

Do NOT send multi-stage transcript in a single evaluation.

10. Internal Access Controls

Internally, system components must follow:

LLM evaluation service can only read redacted transcript

Rule engine can read raw transcript

Database storing evaluations cannot store raw prompts

Frontend can never access raw LLM prompts

Separation of responsibilities is required.

11. Data Retention & Deletion Rules

Before calling the LLM:

Check company-defined retention policy

If the audio/transcript is flagged for deletion → do NOT evaluate

Once retention time passes → delete audio, transcript, evaluations, metadata

Permanent delete = remove from buckets, databases, caches

12. No Cross-Call Context

LLM cannot receive:

Previous call data

Other customer data

Internal historical performance

Agent personal performance history

Each evaluation is isolated.

13. Legal Disclaimers (Platform-Level)

The system must declare:

“We do not train any models on customer data.”

“We do not retain or log LLM prompts.”

“We redact PII before LLM processing.”

“We only send minimal context required for scoring.”

“We do not expose identifiable customer or agent data to external services.”

“Evaluation outputs contain no sensitive personal identifiers.”

14. Allowed Data Types to Send to LLM

These are safe and allowed:

Redacted transcript text

Step definitions

Stage name

Expected phrases

Rule failures (without real names)

Rubric info

Deterministic evidence (with timestamps, redacted)

Tone analysis (non-identifying)

15. Prohibited Data Types

Never send any of these:

Audio waveform

Real customer or agent names

Phone numbers / email / addresses

Policy documents containing private data

CRM ticket numbers

Full metadata of call or customer

Payment information

Any unredacted PII

Company confidential workflow diagrams

Violation of these = legal and compliance failure.

16. Recommended Redaction Patterns (Minimal Required)

You must implement regex-based detection for:

Names → {{NAME}}
Emails → {{EMAIL}}
Phone numbers → {{PHONE}}
Credit cards → {{CARD_NUMBER}}
Account numbers → {{ACCOUNT_NUMBER}}
Addresses → {{ADDRESS}}
Order IDs → {{ORDER_ID}}
Gov IDs → {{GOV_ID}}