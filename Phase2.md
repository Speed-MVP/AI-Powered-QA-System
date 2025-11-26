Phase 2 — Data Model (DB + Blueprint JSON Schema & Constraints)

This phase defines everything your AI coder needs to implement the database model and the canonical Blueprint JSON payload. No source code — schema, types, constraints, indexes, relationships, migration notes, and implementation guidance only.

1 — High-level design decisions (quick summary)

Use relational DB (Postgres / Neon) for primary storage.

Store blueprint content as normalized rows (stages, behaviors) plus a snapshot JSONB for easy export/restore.

Use JSONB for flexible metadata, phrase lists, and UI hints. Index JSONB with GIN for fast search.

Keep compiler artifacts (FlowVersion, ComplianceRules, RubricTemplate) in existing tables; store mapping from blueprint → compiled artifacts.

Version everything: every published blueprint creates an immutable qa_blueprint_versions snapshot.

Enforce constraints at DB + app level: stage ordering, weight sums, required fields.

Provide audit trail for who changed what and when.

2 — Table definitions (conceptual, fields + types + constraints)
qa_blueprints — master table (one row per blueprint)

Purpose: primary record for a blueprint.

Fields:

id UUID PK

company_id UUID FK → companies (not nullable)

name VARCHAR(255) NOT NULL

description TEXT NULL

status ENUM('draft','published','archived') NOT NULL DEFAULT 'draft'

version_number INT NOT NULL DEFAULT 1

compiled_flow_version_id UUID NULL — FK to internal flow_versions (set after publish)

created_by UUID FK → users

updated_by UUID FK → users

created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()

updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()

metadata JSONB NULL — UI hints, preset name, import source, etc.

Constraints / Indexes:

Unique(company_id, name) OR allow same name across teams? Recommend unique per company.

Index on (company_id, status) for listing.

GIN index on metadata if searched.

qa_blueprint_stages — ordered stages per blueprint

Purpose: store stage order and per-stage weight.

Fields:

id UUID PK

blueprint_id UUID FK → qa_blueprints (not nullable, cascade on delete)

stage_name VARCHAR(150) NOT NULL

ordering_index INT NOT NULL — 1..N; used for UI order

stage_weight DECIMAL(5,2) NULL — percent of total (0-100); optional (system can auto-calc)

metadata JSONB NULL — collapsed UI hint, sample transcript window length, stage color, etc.

created_at, updated_at timestamps

Constraints / Indexes:

Unique(blueprint_id, ordering_index)

Unique(blueprint_id, stage_name) — optional but helpful

Index on blueprint_id for retrieval

Notes:

If stage_weight is null, the app will auto-normalize based on summed behavior weights or evenly distribute.

qa_blueprint_behaviors — atomic behaviors inside stages

Purpose: store behaviors; this is the system’s atomic rule unit.

Fields:

id UUID PK

stage_id UUID FK → qa_blueprint_stages (not nullable, cascade on delete)

behavior_name VARCHAR(255) NOT NULL

description TEXT NULL — guidance for reviewers / examples

behavior_type ENUM('required','optional','forbidden','critical') NOT NULL DEFAULT 'required'

detection_mode ENUM('semantic','exact_phrase','hybrid') NOT NULL DEFAULT 'semantic'

phrases JSONB NULL — array of strings or array of objects {text, match_type}; only used if detection_mode != semantic

weight DECIMAL(5,2) NOT NULL DEFAULT 0 — weight contribution within stage (0-100)

critical_action ENUM('fail_stage','fail_overall','flag_only') NULL — only relevant if behavior_type='critical'

ui_order INT NOT NULL DEFAULT 0 — UI ordering within a stage

metadata JSONB NULL — e.g., suggested synonyms, sample utterances, language hints, tone constraints

created_at, updated_at timestamps

Constraints / Indexes:

Unique(stage_id, behavior_name) — to prevent duplicates

Index on stage_id for retrieval

GIN index on phrases for phrase search (if needed)

Behavior weight rules (enforced at app level, validated at publish):

Sum(behavior.weight for stage) should be > 0. System will normalize to stage_weight if provided OR normalize across stages so total = 100.

qa_blueprint_versions — published snapshots (immutable)

Purpose: full snapshot of blueprint at publish time for audit / rollback.

Fields:

id UUID PK

blueprint_id UUID FK → qa_blueprints (not nullable)

version_number INT NOT NULL

snapshot JSONB NOT NULL — full blueprint JSON (stages + behaviors + metadata)

compiled_flow_version_id UUID NULL — created by compiler

published_by UUID FK → users

published_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()

Constraints / Indexes:

Unique(blueprint_id, version_number)

GIN index on snapshot if you need partial queries (avoid overuse)

qa_blueprint_compiler_map — mapping to internal artifacts (optional)

Purpose: map blueprint version → generated internal artifact IDs for traceability.

Fields:

id UUID PK

blueprint_version_id UUID FK → qa_blueprint_versions

flow_version_id UUID FK → flow_versions

policy_rules_version_id UUID FK → policy_rules_versions (if generated)

rubric_template_id UUID FK → rubric_templates

created_at TIMESTAMP

This table makes rollback and audit trivial.

qa_blueprint_audit_logs — optional per-change log (if more granular than versions)

Purpose: store per-change diffs, who changed what and why.

Fields:

id UUID PK

blueprint_id UUID FK

changed_by UUID FK → users

change_type ENUM('create','update','delete','publish')

change_summary TEXT — short human notes

change_diff JSONB — optional diff patch

created_at TIMESTAMP

3 — JSON schema for Blueprint payload (canonical spec)

Provide this as the authoritative API payload for UI ↔ server.

Top-level fields (required): name, stages (non-empty array)

Minimal example expanded (explanatory):

{
  "name": "Standard Support Blueprint",
  "description": "Template for general customer support",
  "status": "draft",
  "stages": [
    {
      "stage_name": "Opening",
      "ordering_index": 1,
      "stage_weight": 20,
      "behaviors": [
        {
          "behavior_name": "Greeting",
          "description": "Agent greets customer in opening",
          "behavior_type": "required",
          "detection_mode": "semantic",
          "phrases": null,
          "weight": 5,
          "critical_action": null,
          "metadata": {
              "examples": ["Hi, good morning", "Hello, how can I help?"],
              "suggested_synonyms": ["hello","good morning","good afternoon"]
          }
        },
        {
          "behavior_name": "Disclosure Statement",
          "behavior_type": "critical",
          "detection_mode": "exact_phrase",
          "phrases": ["This call is recorded", "This call may be monitored"],
          "weight": 10,
          "critical_action": "fail_overall"
        }
      ]
    }
  ],
  "metadata": {
    "template_source": "billing_support_v1",
    "language": "en-US"
  }
}


Validation rules for incoming JSON:

name non-empty; stages array length ≥ 1

stage_name non-empty; ordering_index >=1 unique within blueprint

behavior_name non-empty; behavior_type one of allowed enums

If detection_mode ≠ semantic then phrases must be non-empty array of strings

weight numeric >=0; if all behavior weights in blueprint sum to 0, fail publish

If behavior_type == critical then critical_action is required

status only draft at create; publish via explicit endpoint that validates constraints

4 — Constraints, validations & publisher rules (app + DB enforcement)

Enforce these checks BEFORE publish; DB should have defensive constraints where possible.

Publish-time validations (app-level):

At least one stage exists.

Total stage weights sum to 100% (or auto-normalize with user confirmation).

Within each stage, sum(behavior.weights) > 0 — app normalizes behavior weights to stage weight.

No duplicate behavior names in same stage.

Any critical behavior must have critical_action defined.

exact_phrase entries should check for potentially harmful regex or BANNED_WORDS list (security).

phrases length limit (e.g., 200 chars each) and total phrase count limit to avoid prompt explosion.

Language metadata matches model support; warn if blueprint language unsupported.

DB-level constraints:

Unique(blueprint_id, stage_name) and Unique(stage_id, behavior_name) where appropriate.

Not null constraints on essential fields.

Use CHECK constraints for enum validity (if DB supports).

Use triggers or application logic to set updated_at.

5 — Indexing & performance recommendations

Queries to optimize:

List blueprints for company

Fetch blueprint with stages + behaviors (single query)

Get latest published blueprint per company

Sandbox runs: lookup blueprint → compile artifacts quickly

Recommended indexes:

qa_blueprints (company_id, status, updated_at)

qa_blueprint_stages (blueprint_id, ordering_index)

qa_blueprint_behaviors (stage_id, ui_order)

GIN index on qa_blueprints.metadata and qa_blueprint_behaviors.phrases if supporting text search across phrases.

Consider materialized view or denormalized cache table for published_blueprints to speed evaluation lookup (blueprint → compiled_flow_version mapping).

Sharding/partitioning:

Not necessary early. If company count or blueprints explode, partition qa_blueprints by company_id or use tenancy strategies.

Storage sizing:

phrases JSONB small; but qa_blueprint_versions.snapshot may be larger. Archive old snapshots beyond retention period (e.g., 2 years) or compress them.

6 — Migration guidance (legacy → blueprint)

Steps (no code, process steps):

Export legacy templates: Create mapping rules from old models (FlowVersion + PolicyTemplate + RubricTemplate + ComplianceRules) → new Blueprint JSON.

Map FlowStages → stages (preserve order and names).

Map FlowSteps + ComplianceRules → behaviors.

Map Rubric categories/levels → stage weights or behavior weights (distribute scores proportionally).

Map critical rules to behavior_type=critical with critical_action assigned.

Import into qa_blueprints as draft: Each imported blueprint marked status=draft and version_number=1. Admins must review before publish.

QA validation: Run automated validation and human QA (sample 10 recordings) to confirm behavior detection matches previous system.

Publish & compile: When validated, publish blueprint to create compiled FlowVersion. Do not immediately flip production routing; run parallel comparisons for a pilot window.

Rollout toggle: Implement a per-company feature flag to route evaluations to legacy vs compiled blueprint. Flip only after acceptance.

Deprecation: After pilot success, mark legacy templates deprecated and eventually archive.

7 — Security & privacy fields & recommendations

Flags in metadata or root blueprint:

pii_redaction_required boolean

pii_preserve_raw_transcript boolean (default false)

retention_days int (company policy)

Ensure phrases fields are validated for not containing sensitive patterns (e.g., full account numbers) — if they do, warn and require secure handling.

Access control: only users with qa_manager or higher roles can publish. Reviewers can run sandbox but cannot publish.

8 — Example read patterns & recommended API returns

When frontend requests blueprint for edit:

Return blueprint + ordered stages + ordered behaviors in a single payload (no multiple queries). Use a single select with JOIN or single transaction retrieving arrays.

When running evaluation:

Backend should reference qa_blueprints → lookup compiled_flow_version_id (if published) for the compiled artifacts. If not published, return error or run in draft sandbox-only mode.

9 — Edge cases & how to store them

Multi-language blueprints: store language in blueprint metadata; behaviors may include language-specific phrase lists. If multi-language support required, create separate blueprints per language or extend schema with translations object in metadata. Avoid mixing languages in one blueprint.

Large phrase lists: limit phrases per behavior (recommend <= 20). For large lists use external search rules or rule engine resources, not the primary phrases field.

Behavior reuse: allow behaviors to be shared across stages via shared_behavior_id in behavior metadata if needed (advanced). Keep copy-on-write semantics for versions.

10 — Deliverables for your AI coder from Phase 2

Provide these artifacts to your devs (no code included here, but must be produced):

ER diagram (visual) showing all new tables and relationships to flow_versions, policy_rules_versions, rubric_templates.

DDL-like table definitions with types and constraints (for migration team).

JSON schema (full) for blueprint payload and blueprint version snapshot.

Publish-time validation checklist (explicit rules).

Migration mapping doc: legacy model → blueprint fields mapping.

Indexing & performance plan (as above).

Sample blueprint JSONs for 3 templates: Standard Support, Billing Support, Collections.

Final notes — constraints and tradeoffs

Doing heavy logic (weight normalization, phrase pre-processing, language detection) in DB is possible but better in app layer. Keep DB for authoritative storage and constraints; do validation and normalization in backend service to give human-friendly errors.

Store snapshots as JSONB for audit and rollback, not as the canonical edit source. Canonical source should be normalized rows (stages + behaviors) to make queries efficient.

Avoid putting LLM prompt fragments in DB long-term unless you plan to version prompts; if you do, store them in metadata.prompt_template with versioning.