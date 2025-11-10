# Phased Implementation Plan - AI-Optimized (Modular & Sequential)

**Purpose:** This plan is designed for AI coding agents. Each phase has explicit dependencies, clear module boundaries, and minimal cross-phase coupling. Sections are ordered by execution dependency.

---

# PHASE 1: MVP - Agent & Team Directory with CSV Bulk Import (Weeks 1-8)

## 1.1 Database Schema (FOUNDATION - DO THIS FIRST) ✅ COMPLETED

**Status:** ✅ Models created and migration updated to use String(36) and company_id

**New Tables Created:**
- ✅ `teams` table
- ✅ `agent_team_memberships` table  
- ✅ `agent_team_changes` table
- ✅ `import_jobs` table

**Modifications to Existing Tables:**
- ✅ Added `created_by`, `updated_by`, `deleted_at` to `users` table
- ✅ Added `agent_id`, `team_id` to `recordings` table
- ✅ Added `agent_id`, `team_id` to `evaluations` table

**Models Created:**
- ✅ `backend/app/models/team.py` - Team model
- ✅ `backend/app/models/agent_team.py` - AgentTeamMembership, AgentTeamChange models
- ✅ `backend/app/models/import_job.py` - ImportJob model
- ✅ Updated relationships in Company, User, Recording, Evaluation models

**Migration:**
- ✅ Fixed migration `0123456789ab_phase1_agent_team_directory.py` to use String(36) and company_id

**New Tables to Create:**

```sql
-- Teams table
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL,
    deleted_at TIMESTAMP,
    UNIQUE(org_id, name)
);

-- Agent-Team relationships
CREATE TABLE agent_team_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES users(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    role VARCHAR(50) DEFAULT 'agent',  -- 'agent', 'team_lead', 'supervisor'
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    UNIQUE(agent_id, team_id)
);

-- Audit trail for all agent/team changes
CREATE TABLE agent_team_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- 'agent', 'team', 'membership'
    entity_id UUID NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'deleted'
    field_name VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    changed_by UUID NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    org_id UUID NOT NULL,
    INDEX(org_id, changed_at),
    INDEX(entity_id, changed_at)
);

-- Bulk import jobs tracking
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'csv', 'api', 'manual_ui', 'webhook'
    source_platform VARCHAR(50) DEFAULT 'n/a',  -- 'n/a', 'genesys', 'five9', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    file_name VARCHAR(255),
    rows_total INT,
    rows_processed INT DEFAULT 0,
    rows_failed INT DEFAULT 0,
    validation_errors JSONB,  -- Array of error objects
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX(org_id, created_at),
    INDEX(status)
);
```
### Centralized Import Tracking & Future Extensibility

The `import_jobs` table is essential for tracking bulk import activities, providing a unified ledger of all data sources — CSV, Genesys API, webhooks, manual uploads, etc. 

#### Why it's crucial:
- **Audit & Compliance:** Enables full traceability of who uploaded or synchronized data, when, and from which source.
- **Error Handling:** Stores validation errors, partial successes, and allows retries.
- **Future Integrations:** Serves as the cornerstone for all future data sources, including Genesys, Five9, SCIM, or API syncs, without schema changes. 

#### Implementation notes:
- Source type & platform fields allow source-agnostic tracking.
- All sources funnel into the same `agents` and `agent_team_memberships` tables.
- API endpoints remain generic (`/bulk-import`, `/sync/{platform}`), facilitating easy addition of new sources.
- Audit logs (`agent_team_changes`) record all modifications, regardless of origin.

**Conclusion:** Keep `import_jobs` as a lightweight, flexible ledger for all data ingestion methods — vital for compliance, debugging, and future extension, with minimal overhead.

**Modifications to Existing Tables:**

```sql
-- Add these columns to existing 'users' table if not present
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_by UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Add these columns to existing 'recordings' table
ALTER TABLE recordings ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES users(id);
ALTER TABLE recordings ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id);

-- Add these columns to existing 'evaluations' table
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES users(id);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id);
```

**Indexes to Create (for performance):**

```sql
CREATE INDEX idx_teams_org_id ON teams(org_id);
CREATE INDEX idx_agent_team_memberships_agent_id ON agent_team_memberships(agent_id);
CREATE INDEX idx_agent_team_memberships_team_id ON agent_team_memberships(team_id);
CREATE INDEX idx_recordings_agent_id ON recordings(agent_id);
CREATE INDEX idx_evaluations_agent_id ON evaluations(agent_id);
```

**Dependencies:** None (this is the foundation)

**AI Instructions:** Create these tables using Alembic migration. Ensure all UUIDs default to `gen_random_uuid()`, all timestamps default to `NOW()`, and all indexes are created for query performance.

---

## 1.2 Backend Core Services (BUSINESS LOGIC LAYER) ✅ COMPLETED

**Status:** ✅ All services implemented

**Services Created:**
- ✅ `backend/app/services/team_service.py` - TeamService with CRUD and audit logging
- ✅ `backend/app/services/agent_service.py` - AgentService with CRUD and team membership
- ✅ `backend/app/services/agent_team_audit_service.py` - AgentTeamAuditService for audit queries

**Location:** `backend/app/services/`

**Modules to Create:**

### 1.2.1 Team Service

```python
# Pseudo-code for AI agent to implement

class TeamService:
    """Handles team CRUD and audit logging."""
    
    async def create_team(self, org_id: UUID, name: str, created_by: UUID) -> Team:
        """Create a new team. Log to agent_team_changes."""
        # 1. Check if team name already exists for this org (UNIQUE constraint)
        # 2. Insert into teams table
        # 3. Log change: entity_type='team', change_type='created'
        # 4. Return created team
        
    async def get_teams(self, org_id: UUID) -> List[Team]:
        """Get all teams for an org (exclude deleted)."""
        # 1. Query teams WHERE org_id=? AND deleted_at IS NULL
        # 2. Return list
        
    async def get_team_by_id(self, team_id: UUID) -> Team:
        """Get single team by ID."""
        
    async def update_team(self, team_id: UUID, name: str, updated_by: UUID) -> Team:
        """Update team. Log old/new values to audit trail."""
        # 1. Get current team data
        # 2. Update name
        # 3. Log change: change_type='updated', old_value=old_name, new_value=new_name
        # 4. Return updated team
        
    async def delete_team(self, team_id: UUID, deleted_by: UUID) -> None:
        """Soft delete team (set deleted_at)."""
        # 1. Set deleted_at = NOW()
        # 2. Log change: change_type='deleted'
        # 3. Do NOT delete agent_team_memberships (just mark as deleted if needed)
        
    async def get_team_agents(self, team_id: UUID) -> List[Agent]:
        """Get all agents in a team (via agent_team_memberships)."""
        # 1. Query agent_team_memberships WHERE team_id=? AND deleted_at IS NULL
        # 2. Join with users table to get agent details
        # 3. Return list
        
    async def log_change(self, entity_type: str, entity_id: UUID, change_type: str, 
                         field_name: str, old_value: str, new_value: str, 
                         changed_by: UUID, org_id: UUID) -> None:
        """Generic audit logging. Reusable for agent changes too."""
        # Insert into agent_team_changes table
```

### 1.2.2 Agent Service

```python
class AgentService:
    """Handles agent CRUD and agent-team membership."""
    
    async def create_agent(self, org_id: UUID, agent_data: AgentCreate, created_by: UUID) -> Agent:
        """Create a new agent. This is a user with role 'agent'."""
        # 1. Check if user with this email already exists
        # 2. If yes, throw error (or update; depends on business logic)
        # 3. Create user record with role='agent'
        # 4. If team_id provided, add to agent_team_memberships
        # 5. Log changes
        
    async def get_agents(self, org_id: UUID, team_id: Optional[UUID] = None) -> List[Agent]:
        """Get agents, optionally filtered by team."""
        # 1. Query users WHERE role='agent' AND deleted_at IS NULL
        # 2. If team_id, filter via agent_team_memberships
        # 3. Return list
        
    async def update_agent(self, agent_id: UUID, agent_data: AgentUpdate, updated_by: UUID) -> Agent:
        """Update agent details. Log changes."""
        
    async def delete_agent(self, agent_id: UUID, deleted_by: UUID) -> None:
        """Soft delete agent."""
        
    async def assign_agent_to_team(self, agent_id: UUID, team_id: UUID, created_by: UUID) -> None:
        """Add agent to team (create membership)."""
        # 1. Check if already assigned
        # 2. Insert into agent_team_memberships
        # 3. Log change
        
    async def remove_agent_from_team(self, agent_id: UUID, team_id: UUID, deleted_by: UUID) -> None:
        """Remove agent from team (soft delete membership)."""
        # 1. Set deleted_at on membership
        # 2. Log change
```

### 1.2.3 Audit Log Service

```python
class AuditService:
    """Provides audit trail queries."""
    
    async def get_changes(self, org_id: UUID, 
                         agent_id: Optional[UUID] = None,
                         team_id: Optional[UUID] = None,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None,
                         limit: int = 100) -> List[AuditLog]:
        """Query agent_team_changes with filters."""
        # Build query dynamically based on filters
        # Order by changed_at DESC
        # Limit to avoid large result sets
```

**Dependencies:** Database tables (1.1)

**AI Instructions:** Implement these services using async/await pattern. All methods that modify data should call `log_change()` to audit trail. Wrap database operations in transactions for data consistency. Use parameterized queries (no SQL injection).

---

## 1.3 Backend CSV Bulk Import Service (CRITICAL FOR MVP)

**Location:** `backend/services/csv_import_service.py`

**Modules:**

### 1.3.1 CSV Parser & Validator

```python
class CSVImportService:
    """Handles CSV parsing, validation, column mapping, and upsert."""
    
    async def start_import_job(self, org_id: UUID, file_path: str, 
                               created_by: UUID) -> ImportJob:
        """Create import job record. Kick off background task."""
        # 1. Create import_jobs record with status='pending'
        # 2. Return job with job_id
        # 3. Trigger background task: process_import_job_async(job_id)
        
    async def process_import_job_async(self, job_id: UUID) -> None:
        """Background task to process CSV import. Updates import_jobs record."""
        # 1. Set status='processing'
        # 2. Read CSV file
        # 3. Parse & validate rows
        # 4. Upsert agents and teams
        # 5. Log all changes to agent_team_changes
        # 6. Update import_jobs: status='completed', rows_processed, rows_failed, errors
        
    async def parse_csv_file(self, file_path: str) -> List[Dict]:
        """Read CSV, return list of row dicts."""
        # Use csv.DictReader to read file
        # Validate columns exist: 'agent_name', 'email', 'team_name' (minimum required)
        # Return rows
        
    async def validate_and_map_row(self, row: Dict, org_id: UUID) -> Tuple[bool, AgentData, str]:
        """Validate a single CSV row. Return (is_valid, agent_data, error_msg)."""
        # 1. Check required fields: agent_name, email, team_name
        # 2. Validate email format
        # 3. Check if team_name exists (or create team if not exists)
        # 4. Return (True, AgentData(...)) if valid
        # 5. Return (False, None, error_msg) if invalid
        
    async def upsert_agent_from_csv(self, agent_data: AgentData, created_by: UUID, 
                                     org_id: UUID) -> Tuple[bool, str]:
        """Upsert agent by email. Log all changes. Return (success, error_msg)."""
        # 1. Query users WHERE email=? AND deleted_at IS NULL
        # 2. If exists: update name, assign to team if different
        # 3. If not exists: create new user
        # 4. Log all changes to agent_team_changes
        # 5. Return (True, "") if success
        
    async def get_import_job_status(self, job_id: UUID) -> ImportJob:
        """Get status of import job (for polling from frontend)."""
        # Query import_jobs by job_id
```

**Data Structures:**

```python
@dataclass
class ImportJob:
    id: UUID
    org_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    rows_total: int
    rows_processed: int
    rows_failed: int
    validation_errors: List[Dict]  # [ { row_num, field, error }, ... ]
    created_at: datetime
    completed_at: Optional[datetime]

@dataclass
class AgentData:
    agent_name: str
    email: str
    employee_id: Optional[str]
    team_name: str
```

**Dependencies:** TeamService, AgentService, AuditService (1.2)

**AI Instructions:** 
- Use pandas or csv module for CSV reading (not reinventing the wheel)
- Validate email format using regex
- Use a background task queue (e.g., Celery or FastAPI BackgroundTasks) to process imports asynchronously
- Return job_id immediately so frontend can poll for status
- Store validation errors as JSON array in import_jobs table for later review
- Handle file uploads to temp storage; clean up after processing

---

## 1.4 Backend API Endpoints

**Location:** `backend/routers/teams.py`, `backend/routers/agents.py`, `backend/routers/imports.py`

**Endpoints:**

### Teams

```python
# GET /teams
@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(org_id: UUID, current_user: User = Depends(get_current_user)):
    """List all teams for org. Supervisor+ only."""
    # Call TeamService.get_teams(org_id)

# POST /teams
@router.post("/teams", response_model=TeamResponse)
async def create_team(org_id: UUID, team_in: TeamCreate, 
                     current_user: User = Depends(get_current_user)):
    """Create new team. Supervisor+ only."""
    # Call TeamService.create_team(org_id, team_in.name, current_user.id)

# GET /teams/{team_id}
@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: UUID, current_user: User = Depends(get_current_user)):
    """Get single team."""
    
# PUT /teams/{team_id}
@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(team_id: UUID, team_in: TeamUpdate, 
                     current_user: User = Depends(get_current_user)):
    """Update team. Supervisor+ only."""
    
# DELETE /teams/{team_id}
@router.delete("/teams/{team_id}")
async def delete_team(team_id: UUID, current_user: User = Depends(get_current_user)):
    """Soft delete team. Supervisor+ only."""
    
# GET /teams/{team_id}/agents
@router.get("/teams/{team_id}/agents", response_model=List[AgentResponse])
async def get_team_agents(team_id: UUID, current_user: User = Depends(get_current_user)):
    """Get all agents in team."""
    # Call TeamService.get_team_agents(team_id)
```

### Agents

```python
# GET /agents
@router.get("/agents", response_model=List[AgentResponse])
async def get_agents(org_id: UUID, team_id: Optional[UUID] = None, 
                    current_user: User = Depends(get_current_user)):
    """List agents, optionally filtered by team."""
    # Call AgentService.get_agents(org_id, team_id)

# POST /agents
@router.post("/agents", response_model=AgentResponse)
async def create_agent(org_id: UUID, agent_in: AgentCreate, 
                      current_user: User = Depends(get_current_user)):
    """Create single agent. Supervisor+ only."""
    
# GET /agents/{agent_id}
@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, current_user: User = Depends(get_current_user)):
    """Get agent details."""
    
# PUT /agents/{agent_id}
@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: UUID, agent_in: AgentUpdate, 
                      current_user: User = Depends(get_current_user)):
    """Update agent. Supervisor+ only."""
    
# DELETE /agents/{agent_id}
@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: UUID, current_user: User = Depends(get_current_user)):
    """Soft delete agent. Supervisor+ only."""
```

### Bulk Import (CSV)

```python
# POST /agents/bulk-import
@router.post("/agents/bulk-import")
async def upload_csv_import(org_id: UUID, file: UploadFile = File(...), 
                           current_user: User = Depends(get_current_user)):
    """Upload CSV file. Supervisor+ only. Returns job_id for polling."""
    # 1. Save file to temp storage
    # 2. Call CSVImportService.start_import_job(org_id, file_path, current_user.id)
    # 3. Return { job_id, status: 'processing' }
    
# GET /agents/bulk-import/{job_id}
@router.get("/agents/bulk-import/{job_id}")
async def get_import_job_status(job_id: UUID, current_user: User = Depends(get_current_user)):
    """Poll import job status. Returns current progress and any validation errors."""
    # Call CSVImportService.get_import_job_status(job_id)
    # Return ImportJob with status, rows_processed, validation_errors, preview (first 5 processed rows)
```

### Audit Trail

```python
# GET /agents/audit-log
@router.get("/agents/audit-log", response_model=List[AuditLogResponse])
async def get_audit_log(org_id: UUID, 
                       agent_id: Optional[UUID] = None,
                       team_id: Optional[UUID] = None,
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None,
                       limit: int = 100,
                       current_user: User = Depends(get_current_user)):
    """Get immutable audit trail. Supervisor+ only."""
    # Call AuditService.get_changes(org_id, agent_id, team_id, date_from, date_to, limit)
```

**Dependencies:** Services (1.2, 1.3)

**AI Instructions:**
- Add RBAC checks: Only supervisor/admin can call POST/PUT/DELETE endpoints
- Agents can view their own data
- Return 403 Forbidden if unauthorized
- Add request validation using Pydantic models
- Handle file uploads safely (temp storage, cleanup)

---

## 1.5 Frontend Pages (React/TypeScript)

**Location:** `frontend/src/pages/`

### 1.5.1 Teams List Page

**File:** `TeamsListPage.tsx`

**Components:**
- Table: Team name, agent count, created date, created by, actions (Edit, Delete)
- Button: "+ Create Team"
- Button: "+ Bulk Import Agents"
- Pagination/sorting

**Functionality:**
- Load teams on mount
- Delete team (with confirmation)
- Link to create team modal
- Link to bulk import modal

### 1.5.2 Create/Edit Team Modal

**File:** `TeamFormModal.tsx`

**Functionality:**
- Form fields: Team name
- Submit button
- Error handling
- Close button

### 1.5.3 Agents List Page

**File:** `AgentsListPage.tsx`

**Components:**
- Table: Agent name, email, team, created date, actions (Edit, Delete)
- Filter by team (dropdown)
- Button: "+ Add Agent"
- Button: "+ Bulk Import"

### 1.5.4 Bulk Import Modal

**File:** `BulkImportModal.tsx` (CRITICAL FOR MVP)

**Functionality:**
```
Step 1: File Upload
  - File input (accept .csv)
  - Drag-and-drop support
  
Step 2: Column Mapping
  - Show CSV column headers
  - User maps: "Source Column" → "Target Field" (agent_name, email, team_name, employee_id)
  - Visual UI: Dropdowns or drag-drop
  
Step 3: Preview
  - Show first 10 CSV rows
  - Highlight validation errors in red
  - Show mapping preview (e.g., "Column 'Full Name' → agent_name")
  
Step 4: Confirm & Import
  - Button: "Import"
  - Show progress bar (polling job_id)
  - On completion: Show summary (X rows imported, Y errors)
  - Link to errors (downloadable CSV)
```

**API Calls:**
- POST `/agents/bulk-import` (upload file)
- GET `/agents/bulk-import/{job_id}` (poll status, repeat every 2 seconds)
- On complete: Refresh agents list

### 1.5.5 Audit Trail Page

**File:** `AuditTrailPage.tsx`

**Functionality:**
- Table: Entity ID, entity type, change type, field, old value, new value, changed by, timestamp
- Filters: Date range, entity type (Agent/Team/Membership)
- Sort by timestamp (descending)
- Export to CSV button

**API Calls:**
- GET `/agents/audit-log?org_id={org_id}&date_from={}&date_to={}&limit=100`

### 1.5.6 Basic Supervisor Dashboard

**File:** `SupervisorDashboard.tsx`

**Components:**
- KPI cards: Total teams, total agents, total evaluations (if evaluations table populated)
- Quick stats: Last agent added, last team created
- Recent activity (last 5 audit log entries)

**API Calls:**
- GET `/teams`
- GET `/agents`
- GET `/agents/audit-log?limit=5`

**Dependencies:** Backend APIs (1.4)

**AI Instructions:**
- Use React hooks (useState, useEffect, useContext)
- Use TypeScript for type safety
- Handle loading/error states
- Use TanStack Query or SWR for API calls and caching
- Show confirmation dialogs before delete operations
- Poll bulk import job status every 2 seconds; stop when status != 'processing'

---

## 1.6 Testing Strategy

**Unit Tests (Backend Services):**
- `tests/services/test_team_service.py`: Test create, update, delete, get_team_agents
- `tests/services/test_agent_service.py`: Test create, update, delete, assign_to_team
- `tests/services/test_csv_import_service.py`: Test CSV parsing, validation, upsert

**Integration Tests (API Endpoints):**
- `tests/routers/test_teams_api.py`: POST /teams, GET /teams, PUT /teams/{id}, DELETE /teams/{id}
- `tests/routers/test_agents_api.py`: Similar for agents
- `tests/routers/test_bulk_import_api.py`: POST /agents/bulk-import, GET /agents/bulk-import/{job_id}

**E2E Tests (Full Workflow):**
- Create team → Add agent to team → Bulk import agents → Verify audit trail

**Test Data:**
- Fixture: Create org, user (supervisor), team

**AI Instructions:**
- Test happy path: Valid inputs, expected outputs
- Test error cases: Invalid email, duplicate email, missing team, etc.
- Mock database calls where appropriate
- Use pytest for backend tests
- Mock API calls in frontend tests

---

## 1.7 Deployment Checklist for Phase 1

- [ ] Database migrations applied (Alembic)
- [ ] All backend services implemented
- [ ] All API endpoints tested on staging
- [ ] Frontend pages built and deployed to staging
- [ ] E2E tests passing
- [ ] CSV import tested with real CSV files
- [ ] Audit trail verified (all changes logged)
- [ ] RBAC tested (agents can't create teams)
- [ ] Error handling tested (duplicate email, invalid CSV, etc.)
- [ ] Performance tested (bulk import with 1000+ rows)
- [ ] Release notes drafted
- [ ] Deploy to production

---

# PHASE 2: Core Analytics + CSAT/NPS (Weeks 9-16)

**Goal:** Add analytics so supervisors see agent/team performance metrics.

**Database:**
- `customer_feedback` table (CSAT/NPS)
- `speech_metrics` table (AHT, FCR, etc.)
- `agent_daily_metrics` table (aggregated daily stats)

**Backend:**
- CSAT/NPS capture APIs
- Analytics query APIs (FCR, AHT, trends)
- Aggregation jobs (compute daily metrics)

**Frontend:**
- Enhanced supervisor dashboard (KPI cards, leaderboards, trends)
- Agent leaderboard page
- CSAT/NPS input page
- Team analytics page

**Dependencies:** Phase 1 (Agent/Team directory must exist first)

---

# PHASE 3: Advanced Features (Weeks 17-24)

**Goal:** Add compliance, calibration, advanced speech analytics.

**Database:**
- `compliance_packs` table
- `compliance_violations` table
- `call_timeline_events` table
- `calibration_sessions` table

**Dependencies:** Phase 2 (Analytics foundation)

---

# PHASE 4: Enterprise Features (Weeks 25-32)

**Goal:** Security, multilingual, cost controls, knowledge assist.

**Dependencies:** Phase 3

---

# PHASE 5: Integrations (Weeks 33+)

**Goal:** Genesys, Five9, SCIM adapters.

**Dependencies:** Phase 1 (Agent/team directory + import jobs tracking)

**Why Phase 5 has minimal dependency on Phase 1-4:**
- The `import_jobs` table (Phase 1) and `source_type` column are future-proof
- Phase 5 adapters just create new import jobs with `source_type='genesys'` or `source_type='api'`
- All downstream tables (Phase 2+) don't change; they just reference the same `agents` table

---

# CRITICAL NOTES FOR AI CODING AGENT

## Order of Execution (STRICT)

1. **Phase 1.1:** Database schema (all migrations must complete)
2. **Phase 1.2:** Backend services (no APIs yet, just business logic)
3. **Phase 1.3:** CSV import service (depends on services)
4. **Phase 1.4:** API endpoints (depends on services)
5. **Phase 1.5:** Frontend (depends on API endpoints)
6. **Phase 1.6:** Tests (test all of the above)
7. **Phase 1.7:** Deploy to staging/production

**Do NOT start Phase 2 until Phase 1 is complete and tested.**

## Modular Design

Each service, router, and component should be **independently testable**. No spaghetti code.

Example:
- `TeamService` does NOT call API router directly
- `API router` calls `TeamService`
- `Frontend component` calls `API router` via HTTP

## Testing Before Moving Forward

- **After 1.1:** Run migration, verify tables exist
- **After 1.2:** Unit test all services
- **After 1.3:** Integration test CSV import end-to-end
- **After 1.4:** API integration tests
- **After 1.5:** Frontend integration tests (mock API)
- **After 1.6:** Full E2E test in staging

## For Future Flexibility (Phase 5 Integrations)

- The `import_jobs` table MUST have `source_type` and `source_platform` columns
- The CSV import service MUST use generic "validate → upsert" logic, not CSV-specific logic
- All data changes MUST be logged to `agent_team_changes` (reusable for any source)

**Do NOT create CSV-specific code paths that can't be reused for API/webhook imports.**

---

# Summary: What AI Agent Should Code

## Phase 1 Deliverables (8 weeks):

✅ Database: teams, agent_team_memberships, agent_team_changes, import_jobs  
✅ Services: TeamService, AgentService, AuditService, CSVImportService  
✅ APIs: /teams, /agents, /agents/bulk-import, /agents/audit-log  
✅ Frontend: TeamsListPage, AgentsListPage, BulkImportModal, AuditTrailPage, Dashboard  
✅ Tests: Unit + Integration + E2E  
✅ Deployment: Migration + staging test + production deploy  

**AI Agent: You're done when all 7 items above are complete and tested.**