Phase 8 — UI / UX Implementation (Blueprint Canvas, Behavior Cards, Sandbox, Inspector, Human Review)

Purpose: deliver a production-ready, non-technical, task-focused UI for QA managers to create, edit, publish and test QA Blueprints. The UI maps directly to the Blueprint data model and supports the publish → compile → sandbox lifecycle. Design is vertical, checklist-first, minimal cognitive load, accessible, and mobile-friendly where appropriate.

1 — UX principles & rules (must follow)

Users are QA managers (non-technical). Show behaviors inside stages — no node graphs.

One screen = one job: editing a blueprint, running a sandbox, reviewing evaluation.

Minimize clicks for common tasks: add behavior, set required/critical, run test.

Provide immediate, contextual validation and guided fixes.

Visual clarity: use whitespace, clear icons, minimal colors (green/red/amber/neutral).

Explainability: every behavior and violation must show evidence (highlighted transcript snippets with timestamps).

Progressive disclosure: advanced options hidden behind “Advanced” toggles.

Accessibility: keyboard drag/drop, ARIA roles, high contrast, screen reader labels.

Performance: load blueprint fully in one request; avoid multiple sequential fetches.

2 — Main screens & flows
A. Blueprints List (Landing)

Purpose: list, search, create, import templates.

Layout: table with columns — Name, Status, Version, #Stages, Last Updated, Actions (Edit / Publish / Sandbox / Duplicate / Archive).

Quick actions: New Blueprint (Empty / From Template), Import Legacy.

Row actions open modals for quick preview or direct to Blueprint Editor.

B. Blueprint Editor — Canvas (Primary)

Purpose: create/edit blueprint (stages + behaviors).

Layout: three columns:

Left: Stage list (compact) — drag handles for reorder, quick-add stage button.

Center: Vertical Canvas — stacked StageCards (largest area).

Right: Inspector Panel — when a stage or behavior selected, show editable properties.

Top toolbar: Blueprint name (inline editable), status badge (Draft/Published), Save (auto-save indicator), Publish (button with checklist validation), Version number, Help/Docs.

Bottom bar: Scoring Summary (compact): pie/stack bar showing stage weights and total = 100%.

C. Behavior Editor (inline modal or inspector)

Purpose: create/edit behavior.

Inputs (minimal): Name, Type (Required/Optional/Forbidden/Critical), Detection Mode (Semantic/Exact/Hybrid), Phrases (conditional), Weight slider/input, Critical action (dropdown: fail_stage/fail_overall/flag_only), Notes (internal).

Quick test button within behavior: “Test on sample transcript”.

D. Sandbox (Test) Page / Modal

Purpose: run transcript/audio against draft/published blueprint and see results.

Layout: left — audio player + transcript (with diarization); center — Evaluation summary (score, confidence, require_review flag); right — Stage breakdown with behavior results and evidence.

Actions: Replay, Jump-to-evidence (click evidence to move audio), Export report (CSV/PDF), Add to training set.

Mode: Sync for transcript; Async (job) for audio upload — show run status.

E. Publish Flow

Click Publish → open Publish modal with checklist (validation results). If any fatal errors, prevent publish and link to fixes. Publish triggers background compile job; show progress modal and job status page link.

F. Human Review UI

Purpose: show side-by-side AI vs Human; allow corrections, notes, and submitting training data.

Layout: left — transcript with highlighted evidence and AI marks; center — AI evaluation summary; right — editable human scoring panel (behavior checkboxes, comments).

Buttons: Submit, Mark as Resolved, Flag for Escalation.

3 — Canvas & Component Architecture (component list + responsibilities)
Atomic components

Icon (shared)

Button (primary/secondary/ghost)

InputText, Textarea, Select, Toggle, Slider (weight)

Modal, Toast, ConfirmDialog

Spinner, Skeleton (loading)

Composite components

StageList (left column) — list of StageListItem with drag handle

StageCard (center canvas) — header (stage name, weight), behaviors list, +Add Behavior

BehaviorCard — summary row with icon, type badge, weight chip, quick actions (edit, test, delete)

BehaviorEditor (modal/inspector) — full behavior form

InspectorPanel (right column) — stage/behavior properties, validation warnings, quick actions

ScoringSummary (bottom) — pie or stacked bar and validation status

PublishModal — validation checklist & Publish button

SandboxRunner — upload/select recording, run, show result

EvaluationViewer — full evaluation results with evidence links

TranscriptPlayer — audio + transcript with highlighted evidence, time sync

TemplateLibrary — template cards with import button

ValidationBanner — shows publish blockers & warnings

HumanReviewEditor — side-by-side editor for reviewer

4 — Page & component behaviors (detailed interactions)
Blueprint Editor — Canvas interactions

Drag stage up/down: reorder triggers PUT /api/blueprints/{id} (batch update) or local reorder + Save.

Click Stage header: expands StageCard into edit mode and populates InspectorPanel.

Click +Add Behavior: opens BehaviorEditor inline under stage (auto-focus name).

BehaviorCard quick toggles:

Click Required/Optional badge cycles through types.

Weight slider on hover shows exact percent and updates ScoringSummary live.

Test button opens Sandbox modal with last selected recording or prompt to upload/select sample.

Auto-save: debounce 2s after edits; show last saved timestamp. Use optimistic UI and show conflict toast when 409 returned.

Behavior Editor specifics

Detection Mode switch:

semantic: phrases input hidden; show helper copy: “Recommended for flexible wording”

exact_phrase: show multi-line phrases input; support paste & tokenize; validate duplicates; show phrase count.

hybrid: show both.

Weight slider:

Visual constraints: min 0, max stage_weight; show suggested values; clicking “Auto-distribute” normalizes sibling weights.

Critical behavior toggle:

On toggle to critical open small confirm (two steps) showing consequences (auto-fail stage/overall).

Save closes editor; unsaved changes prompt if navigating away.

InspectorPanel interactions

When a Stage selected: show Stage-level weight (editable), sample window setting, add/remove behaviors.

When a Behavior selected: show Behavior properties with sample utterance suggestions, synonyms, AI-suggested phrases (from PolicyRuleBuilder suggestions) with “Apply suggestion” button.

Show immediate validation warnings (e.g., stage weight imbalance, duplicated phrase) and clickable “Fix” actions.

Validation UX

Publish button disabled until critical validations pass.

Validation types:

Errors (red): block publish — show panel with each error and link to relevant stage/behavior.

Warnings (amber): show in toolbar and allow publish after “I understand” checkbox.

Real-time validation: on major changes run local validation; full validation runs on Publish (server-side) and can produce additional errors.

5 — Sandbox UX details
Start

Button Run Test in top toolbar or per-behavior Test action.

Input options

Choose last recordings (recent uploads) or Upload audio file (support formats). Or paste transcript (text area).

Option: choose Use draft blueprint or Use published compiled version.

Running

For transcript input: run synchronously and show result in <2s for short input.

For audio: show job queued; poll GET /api/blueprints/{id}/sandbox-runs/{run_id} with progress bar.

Results view

Top: overall score, pass/fail, confidence meter.

Left: audio player + transcript with highlights; clicking highlight scrolls transcript and jumps audio.

Middle: Stage list with stage_score and stage_confidence. Expand stage to see behaviors.

Right: Behavior detail card with evidence and links to transcript timestamps.

Footer: Actions: Create human review, Export report, Save as training example.

Explainability

Each behavior shows evidence snippet with timestamp and LLM reason (if allowed). Show “Why did AI mark this as satisfied?” toggles to reveal LLM short rationale (<=200 chars).

6 — Human Review UI details
Reviewer workflow

Reviewer dashboard lists pending reviews ordered by priority (critical first, low confidence second).

Opening review loads EvaluationViewer with AI output and editable controls.

Reviewer can:

Toggle behavior satisfied/unsatisfied/partial.

Adjust behavior weight or score? (disallowed normally; only QA managers can change weights).

Add reviewer notes (mandatory if score changed > X).

Submit corrections; system creates human_review entry and training_example.

Side-by-side view

Left: transcript & audio with AI highlights.

Right: form with AI values prefilled; reviewer edits and saves.

Show delta summary before submit: list of changed behaviors and impact on overall score.

Audit & trace

Save human review snapshot, link to evaluation and user. Provide “undo” for admins within 24 hours.

7 — Publish flow & job UI
Publish modal

Shows validation checklist: green checks and red blockers. Each item clickable to open relevant editor.

Option: Force normalize weights with explanation and logs warning. Require I confirm checkbox.

Click Publish:

Call POST /api/blueprints/{id}/publish → receive job_id.

Show compile job modal with progress (poll publish_status), logs tail, errors/warnings summary.

On success show "Blueprint published" with compiled_flow_version_id and link to run sandbox on published version.

Job UI specifics

Show timeline: validation → mapping → policy rule generation → artifact persistence → done.

If failed: show errors with Fix link and Retry button (admin only) and downloadable job log.

8 — Templates & onboarding
Templates library

Sidebar or modal: cards for templates (Standard Support, Billing, Collections, Technical).

Each card has Preview (shows stages + top behaviors) and Import (creates draft blueprint).

Template metadata: recommended industries, estimated setup time, sample scoring profile.

Onboarding flow (first-time)

Guided tour overlay:

Step 1: Create new blueprint or pick template.

Step 2: Explain stage vs behavior, add behavior example.

Step 3: Run sandbox on sample call.

Step 4: Publish & test.

Provide “Sample calls” dataset for immediate sandbox testing.

9 — Responsive & accessibility details
Responsive

Desktop: three-column layout (Stage list / Canvas / Inspector).

Tablet: two-column (Canvas + Inspector modal).

Mobile: single column; Stage list as top accordion; Behavior Editor full-screen modal.

Avoid heavy drag-and-drop on mobile; provide up/down arrows for reorder.

Accessibility

Keyboard support:

Tab navigation through stage/behavior cards.

Arrow keys for reorder (hold modifier).

Enter opens editor; Esc cancels.

ARIA:

Role list for StageList, listitem for StageCard.

BehaviorCard includes aria-labelledby & aria-describedby linking to name & description.

Colors:

WCAG contrast >= 4.5:1.

Avoid color-only indicators: include icons & text.

Screen reader:

Announce “Stage moved to position 2” on reorder.

Announce validation errors when publish attempted.

10 — State management & data flow
Frontend stack recommendations (for AI coder)

React 19 + TypeScript. Use Zustand for stores (policyStore, blueprintStore), matching your backend plan.

Centralized API client lib/api.ts to manage JWT, retries, Idempotency-Key, and websockets for job updates.

Use optimistic updates for edits with ETag/If-Match to avoid overwrite conflicts.

Use local validation before server calls; show server validation results after publish.

Key stores

blueprintStore: current blueprint, dirty flags, etag, lastSavedAt.

uiStore: selectedStageId, selectedBehaviorId, modal states.

sandboxStore: run status, lastRunId, lastResult.

Events & hooks

onBlueprintSave → POST/PUT; update store; push saved event.

onPublish → POST publish, open job modal, subscribe to job updates via poll or websocket.

onSandboxRun → create run; poll run status; display result.

11 — Component props / API contracts (example)
StageCard props
interface StageCardProps {
  stage: Stage;
  behaviors: Behavior[];
  onSelectStage(stageId: string): void;
  onAddBehavior(stageId: string): void;
  onReorderBehavior(stageId: string, fromIndex: number, toIndex: number): void;
}

BehaviorEditor props
interface BehaviorEditorProps {
  behavior?: Behavior; // undefined for new
  stageId: string;
  onSave(behavior: BehaviorInput): Promise<void>;
  onCancel(): void;
}

SandboxRunner contract

POST /api/blueprints/{id}/sandbox-evaluate returns run_id or sync result.

Poll /api/blueprints/{id}/sandbox-runs/{run_id} for status and result.

12 — Visual style & microcopy guidelines
Visual

Base UI: neutral gray palette + Tailwind defaults. Use 2 accent colors: primary (blue) and alert (red/orange).

Card corners: rounded-lg.

Shadow: soft (shadow-md) for stage cards; stronger shadow for modals.

Motion: small easing on drag and section expand / collapse (framer-motion optional).

Microcopy (critical)

Behavior Type tooltip: “Required — expected every call. Optional — good to have. Forbidden — must not be said. Critical — missing this triggers immediate action.”

Detection Mode tooltip: “Semantic: AI checks meaning (recommended). Exact: matches specific phrases (legal/compliance). Hybrid: both.”

Publish checklist item: “Stage weights must sum to 100% — click Auto-fix to evenly distribute weights.”

Sandbox empty state: “No recordings yet — upload or use sample calls.”

13 — Error handling & validation UX

Inline errors for form fields (phrases length, duplicate phrase).

Global validation banner for publish blockers with link actions.

Conflict (ETag 409): show modal with “View remote changes” and options: Overwrite / Merge / Cancel.

Server errors: show friendly message with request_id and “Contact support” link.

14 — Testing & QA (frontend)

Unit tests for components using Vitest + React Testing Library.

Integration tests for flows using Playwright:

Create blueprint → add stages & behaviors → run sandbox → publish flow (simulate job success via mock).

Human review flow: reviewer edits behaviors and submits.

Accessibility tests: axe-core integration; run as part of CI.

E2E test data: sample blueprint and transcripts included in repo.

15 — Metrics & telemetry (UI)

Track user interactions for product analytics:

Blueprint created, published, duplicated, deleted.

Behavior added/edited/deleted.

Sandbox run started/completed/error.

Publish job started/succeeded/failed.

Time to first publish for new customers.

Feature usage: templates imported, auto-normalize invoked.

Emit events to analytics (server-side or client-side) with company_id & user_id for product insights.

16 — Deliverables for frontend devs

Component library and design tokens (Tailwind config with color tokens, spacing, border radius).

Full page wireframes for Blueprint Editor, Sandbox, Publish modal, Human Review UI. (annotated)

Prop interfaces for major components (see examples).

API integration stubs for CRUD, publish, sandbox, job status.

Playwright E2E scripts for main flows.

Accessibility checklist & automated tests.

Client telemetry plan and event names.

Localization hooks (i18n) for microcopy.

17 — Quick checklist for release (UX QA)

 All publish validation messages map to UI anchors (click-to-fix).

 Sandbox highlights evidence with jump-to-audio working.

 Critical toggle requires two-step confirmation.

 Auto-save works and conflict flow tested.

 Templates import creates editable drafts.

 Human review edits produce training entry.

 Keyboard accessibility for drag & drop.

 Mobile view allows reordering with up/down controls.

 E2E tests pass and coverage includes fail/fallback scenarios.