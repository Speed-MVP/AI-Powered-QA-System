// API client for FastAPI backend
// In production, VITE_API_URL must be set in Vercel environment variables
// For local development, defaults to http://localhost:8000
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ApiError {
  detail: string
}

export interface Team {
  id: string
  company_id: string
  name: string
  created_at?: string
  updated_at?: string
  created_by?: string | null
  updated_by?: string | null
}

export interface AgentTeamMembership {
  membership_id: string
  team_id: string
  team_name?: string | null
  role?: string | null
}

export interface Agent {
  id: string
  company_id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  team_memberships: AgentTeamMembership[]
}

export interface ImportJob {
  id: string
  company_id: string
  status: string
  file_name?: string | null
  rows_total?: number | null
  rows_processed?: number | null
  rows_failed?: number | null
  validation_errors?: Array<Record<string, any>> | null
  created_by: string
  created_at: string
  completed_at?: string | null
}

export interface AuditLogEntry {
  id: string
  company_id: string
  entity_type: string
  entity_id: string
  change_type: string
  field_name?: string | null
  old_value?: string | null
  new_value?: string | null
  changed_by: string
  changed_at: string
}

// Legacy PolicyTemplate interface removed - use FlowVersion + RubricTemplate + ComplianceRule instead

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token)
      } else {
        localStorage.removeItem('auth_token')
      }
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Always sync token from localStorage before making request
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken !== this.token) {
        this.token = storedToken
      }
    }

    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // Add token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    // Merge with existing headers from options
    if (options.headers) {
      Object.assign(headers, options.headers)
    }

    // Remove Content-Type for FormData requests
    if (options.body instanceof FormData) {
      delete headers['Content-Type']
    }

    let response: Response
    try {
      response = await fetch(url, {
        ...options,
        headers,
      })
    } catch (fetchError: any) {
      // Handle network errors (connection refused, CORS, etc.)
      if (fetchError.message?.includes('Failed to fetch') || fetchError.name === 'TypeError') {
        throw new Error(`Cannot connect to backend server at ${this.baseUrl}. Please make sure the backend is running.`)
      }
      throw fetchError
    }

    if (!response.ok) {
      // Handle 401 unauthorized - clear token
      if (response.status === 401) {
        this.setToken(null)
        throw new Error('Session expired. Please log in again.')
      }

      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(error.detail || 'Request failed')
    }

    return response.json()
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const data = await this.request<{
      access_token: string
      token_type: string
      user_id: string
    }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(data.access_token)
    return data
  }

  async getCurrentUser() {
    return this.request<{
      id: string
      email: string
      full_name: string
      role: string
      company_id: string
    }>('/api/auth/me')
  }

  // Recording endpoints
  async getSignedUploadUrl(fileName: string) {
    // Note: This should be a POST request but with file_name as query param
    // The backend expects file_name as a query parameter
    return this.request<{
      signed_url: string
      file_url: string
      file_name: string
    }>(`/api/recordings/signed-url?file_name=${encodeURIComponent(fileName)}`, {
      method: 'POST',
    })
  }

  async uploadRecording(fileName: string, fileUrl: string) {
    return this.request<{
      id: string
      file_name: string
      file_url: string
      status: string
      uploaded_at: string
    }>('/api/recordings/upload', {
      method: 'POST',
      body: JSON.stringify({
        file_name: fileName,
        file_url: fileUrl,
      }),
    })
  }

  async uploadFileDirect(file: File) {
    // Get token from instance or localStorage (use same key)
    const token = this.token || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null)
    
    if (!token) {
      throw new Error('Not authenticated. Please log in first.')
    }

    // Always use backend upload endpoint - it handles large files with streaming
    // The backend uses temporary files and streaming to handle files larger than Cloud Run's 32MB limit
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/api/recordings/upload-direct`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      
      // Handle 401 unauthorized - clear token
      if (response.status === 401) {
        this.setToken(null)
        throw new Error('Session expired. Please log in again.')
      }
      
      // Handle 413 error with helpful message
      if (response.status === 413) {
        throw new Error('File is too large. Cloud Run has a 32MB limit. Please contact support to configure CORS on GCP Storage bucket for larger files, or split the file into smaller chunks.')
      }
      
      throw new Error(error.detail || 'Upload failed')
    }

    return response.json()
  }

  async getRecording(recordingId: string) {
    return this.request<{
      id: string
      file_name: string
      file_url: string
      status: string
      duration_seconds: number | null
      error_message: string | null
      uploaded_at: string
      processed_at: string | null
    }>(`/api/recordings/${recordingId}`)
  }

  // Evaluation endpoints
  async getEvaluation(recordingId: string) {
    return this.request<{
      id: string
      recording_id: string
      flow_version_id: string | null
      rubric_template_id: string | null
      overall_score: number
      resolution_detected: boolean
      resolution_confidence: number
      customer_tone?: {
        primary_emotion: string
        confidence: number
        description: string
        emotional_journey?: Array<{
          segment: string
          emotion: string
          intensity: string
          evidence: string
        }>
      }
      llm_analysis: any
      status: string
      created_at: string
      category_scores: Array<{
        id: string
        category_name: string
        score: number
        feedback: string | null
      }>
    }>(`/api/evaluations/${recordingId}`)
  }

  async getTranscript(recordingId: string) {
    return this.request<{
      recording_id: string
      transcript_text: string
      diarized_segments: Array<{
        speaker: string
        text: string
        start: number
        end: number
      }> | null
      confidence: number | null
    }>(`/api/evaluations/${recordingId}/transcript`)
  }

  async listRecordings(params?: { skip?: number; limit?: number; status?: string }) {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    const query = queryParams.toString()
    return this.request<Array<{
      id: string
      company_id: string
      uploaded_by_user_id: string
      file_name: string
      file_url: string
      duration_seconds: number | null
      status: string
      error_message: string | null
      uploaded_at: string
      processed_at: string | null
    }>>(`/api/recordings/list${query ? `?${query}` : ''}`)
  }

  async deleteRecording(recordingId: string) {
    return this.request<{ message: string }>(`/api/recordings/${recordingId}`, {
      method: 'DELETE',
    })
  }

  async reevaluateRecording(recordingId: string) {
    return this.request<{ message: string; recording_id: string }>(`/api/recordings/${recordingId}/reevaluate`, {
      method: 'POST',
    })
  }

  async getDownloadUrl(recordingId: string) {
    return this.request<{
      download_url: string
      file_name: string
      expires_in_minutes: number
    }>(`/api/recordings/${recordingId}/download-url`)
  }

  // Legacy Policy Template endpoints removed - use FlowVersion + RubricTemplate + ComplianceRule instead

  // Upload file directly to GCP Storage using signed URL
  async uploadFileToStorage(signedUrl: string, file: File): Promise<void> {
    const response = await fetch(signedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`)
    }
  }

  // Human Review endpoints
  async getPendingReviews(params?: { skip?: number; limit?: number }) {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())

    const query = queryParams.toString()
    return this.request<Array<{
      review_id: string
      evaluation_id: string
      transcript_text: string
      diarized_segments: Array<{
        speaker: string
        text: string
        start: number
        end: number
      }>
      audio_url: string | null
      ai_overall_score: number
      ai_category_scores: Record<string, any>
      ai_violations: Array<any>
      created_at: string
    }>>(`/api/fine-tuning/human-reviews/pending${query ? `?${query}` : ''}`)
  }

  async submitHumanReview(reviewId: string, data: {
    human_overall_score: number
    human_category_scores: Record<string, number>
    ai_score_accuracy: number
  }) {
    return this.request<{ message: string }>(`/api/fine-tuning/human-reviews/${reviewId}/submit`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async createTestHumanReview(evaluationId: string) {
    return this.request<{ message: string; review_id: string }>(`/api/fine-tuning/human-reviews/test-create`, {
      method: 'POST',
      body: JSON.stringify({ evaluation_id: evaluationId }),
    })
  }

  async getEvaluationWithTemplate(evaluationId: string) {
    return this.request<{
      id: string
      recording_id: string
      flow_version_id: string | null
      rubric_template_id: string | null
      overall_score: number
      resolution_detected: boolean
      resolution_confidence: number
      customer_tone: any
      llm_analysis: any
      status: string
      created_at: string
      category_scores: Array<{
        id: string
        category_name: string
        score: number
        feedback: string | null
      }>
      flow_version: {
        id: string
        name: string
        description: string | null
        stages: Array<{
          id: string
          name: string
          order: number
          steps: Array<{
            id: string
            name: string
            order: number
            description: string | null
          }>
        }>
      } | null
      rubric_template: {
        id: string
        name: string
        description: string | null
        categories: Array<{
          id: string
          name: string
          description: string | null
          weight: number
          pass_threshold: number
          level_definitions: Array<{
            name: string
            min_score: number
            max_score: number
            description?: string
            label?: string
          }>
          mappings: Array<{
            id: string
            target_type: string
            target_id: string
            contribution_weight: number
            required_flag: boolean
          }>
        }>
      } | null
    }>(`/api/evaluations/${evaluationId}/with-template`)
  }

  // Team endpoints
  async listTeams() {
    return this.request<Team[]>('/api/teams')
  }

  async createTeam(data: { name: string }) {
    return this.request<Team>('/api/teams', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateTeam(teamId: string, data: { name: string }) {
    return this.request<Team>(`/api/teams/${teamId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteTeam(teamId: string) {
    return this.request<{ status: string }>(`/api/teams/${teamId}`, {
      method: 'DELETE',
    })
  }

  // Agent endpoints
  async listAgents(params?: { teamId?: string }) {
    const queryParams = new URLSearchParams()
    if (params?.teamId) {
      queryParams.append('team_id', params.teamId)
    }
    const query = queryParams.toString()
    return this.request<Agent[]>(`/api/agents${query ? `?${query}` : ''}`)
  }

  async createAgent(data: { full_name: string; email: string; team_id?: string | null }) {
    return this.request<Agent>('/api/agents', {
      method: 'POST',
      body: JSON.stringify({
        full_name: data.full_name,
        email: data.email,
        team_id: data.team_id || undefined,
      }),
    })
  }

  async updateAgent(agentId: string, data: { full_name?: string; email?: string; team_id?: string | null }) {
    return this.request<Agent>(`/api/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify({
        full_name: data.full_name,
        email: data.email,
        team_id: data.team_id || undefined,
      }),
    })
  }

  async deleteAgent(agentId: string) {
    return this.request<{ status: string }>(`/api/agents/${agentId}`, {
      method: 'DELETE',
    })
  }

  async getAuditLog(params?: {
    agentId?: string
    teamId?: string
    entityType?: string
    dateFrom?: string
    dateTo?: string
    limit?: number
  }) {
    const queryParams = new URLSearchParams()
    if (params?.agentId) queryParams.append('agent_id', params.agentId)
    if (params?.teamId) queryParams.append('team_id', params.teamId)
    if (params?.entityType) queryParams.append('entity_type', params.entityType)
    if (params?.dateFrom) queryParams.append('date_from', params.dateFrom)
    if (params?.dateTo) queryParams.append('date_to', params.dateTo)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    const query = queryParams.toString()
    return this.request<AuditLogEntry[]>(`/api/agents/audit-log${query ? `?${query}` : ''}`)
  }

  async uploadAgentImport(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return this.request<ImportJob>('/api/agents/bulk-import', {
      method: 'POST',
      body: formData,
    })
  }

  async getImportJob(jobId: string) {
    return this.request<ImportJob>(`/api/agents/bulk-import/${jobId}`)
  }

  async getSupervisorEvaluations(params?: {
    status?: string
    limit?: number
    offset?: number
  }) {
    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    const query = queryParams.toString()
    return this.request<{
      success: boolean
      data: Array<Record<string, any>>
      pagination: { total: number; limit: number; offset: number; has_more: boolean }
    }>(`/api/supervisor/evaluations${query ? `?${query}` : ''}`)
  }

  // FlowVersion endpoints (Phase 1)
  async listFlowVersions() {
    return this.request<Array<{
      id: string
      company_id: string
      name: string
      description: string | null
      is_active: boolean
      version_number: number
      created_at: string
      updated_at: string
      stages: Array<{
        id: string
        flow_version_id: string
        name: string
        order: number
        steps: Array<{
          id: string
          stage_id: string
          name: string
          description: string | null
          required: boolean
          expected_phrases: string[]
          timing_requirement: { enabled: boolean; seconds: number } | null
          order: number
        }>
      }>
    }>>('/api/flow-versions')
  }

  async createFlowVersion(data: { name: string; description?: string }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      is_active: boolean
    }>('/api/flow-versions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateFlowVersion(flowVersionId: string, data: { name?: string; description?: string; is_active?: boolean }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      is_active: boolean
    }>(`/api/flow-versions/${flowVersionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteFlowVersion(flowVersionId: string) {
    return this.request<{ message: string }>(`/api/flow-versions/${flowVersionId}`, {
      method: 'DELETE',
    })
  }

  async createStage(flowVersionId: string, data: { name: string; order: number }) {
    return this.request<{
      id: string
      name: string
      order: number
    }>(`/api/flow-versions/${flowVersionId}/stages`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateStage(flowVersionId: string, stageId: string, data: { name?: string; order?: number }) {
    return this.request<{
      id: string
      name: string
      order: number
    }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteStage(flowVersionId: string, stageId: string) {
    return this.request<{ message: string }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}`, {
      method: 'DELETE',
    })
  }

  async reorderStages(flowVersionId: string, stageIds: string[]) {
    return this.request<{ message: string }>(`/api/flow-versions/${flowVersionId}/reorder-stages`, {
      method: 'POST',
      body: JSON.stringify({ stage_ids: stageIds }),
    })
  }

  async createStep(flowVersionId: string, stageId: string, data: {
    name: string
    description?: string
    required: boolean
    expected_phrases?: string[]
    timing_requirement?: { enabled: boolean; seconds: number } | null
    order: number
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      required: boolean
      expected_phrases: string[]
      timing_requirement: { enabled: boolean; seconds: number } | null
      order: number
    }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}/steps`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateStep(flowVersionId: string, stageId: string, stepId: string, data: {
    name?: string
    description?: string
    required?: boolean
    expected_phrases?: string[]
    timing_requirement?: { enabled: boolean; seconds: number } | null
    order?: number
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      required: boolean
      expected_phrases: string[]
      timing_requirement: { enabled: boolean; seconds: number } | null
      order: number
    }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}/steps/${stepId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteStep(flowVersionId: string, stageId: string, stepId: string) {
    return this.request<{ message: string }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}/steps/${stepId}`, {
      method: 'DELETE',
    })
  }

  async reorderSteps(flowVersionId: string, stageId: string, stepIds: string[]) {
    return this.request<{ message: string }>(`/api/flow-versions/${flowVersionId}/stages/${stageId}/reorder-steps`, {
      method: 'POST',
      body: JSON.stringify({ step_ids: stepIds }),
    })
  }

  // ComplianceRule endpoints (Phase 2)
  async listComplianceRules(params?: { flow_version_id?: string; active_only?: boolean }) {
    const queryParams = new URLSearchParams()
    if (params?.flow_version_id) queryParams.append('flow_version_id', params.flow_version_id)
    if (params?.active_only) queryParams.append('active_only', 'true')
    const query = queryParams.toString()
    return this.request<Array<{
      id: string
      flow_version_id: string
      title: string
      description: string | null
      severity: string
      rule_type: string
      applies_to_stages: string[]
      params: any
      active: boolean
      created_at: string
    }>>(`/api/compliance-rules${query ? `?${query}` : ''}`)
  }

  async createComplianceRule(data: {
    flow_version_id: string
    title: string
    description?: string
    severity: string
    rule_type: string
    applies_to_stages?: string[]
    params: any
    active?: boolean
  }) {
    return this.request<{
      id: string
      title: string
      description: string | null
      severity: string
      rule_type: string
      params: any
      active: boolean
    }>('/api/compliance-rules', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateComplianceRule(ruleId: string, data: {
    title?: string
    description?: string
    severity?: string
    rule_type?: string
    applies_to_stages?: string[]
    params?: any
    active?: boolean
  }) {
    return this.request<{
      id: string
      title: string
      description: string | null
      severity: string
      rule_type: string
      params: any
      active: boolean
    }>(`/api/compliance-rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteComplianceRule(ruleId: string) {
    return this.request<{ message: string }>(`/api/compliance-rules/${ruleId}`, {
      method: 'DELETE',
    })
  }

  async toggleComplianceRule(ruleId: string) {
    return this.request<{ active: boolean }>(`/api/compliance-rules/${ruleId}/toggle`, {
      method: 'POST',
    })
  }

  // Rubric endpoints (Phase 5)
  async listRubrics(params?: { flow_version_id?: string; policy_template_id?: string; active_only?: boolean }) {
    const queryParams = new URLSearchParams()
    if (params?.flow_version_id) queryParams.append('flow_version_id', params.flow_version_id)
    if (params?.policy_template_id) queryParams.append('policy_template_id', params.policy_template_id)
    if (params?.active_only) queryParams.append('active_only', 'true')
    const query = queryParams.toString()
    return this.request<Array<{
      id: string
      policy_template_id: string | null
      flow_version_id: string
      name: string
      description: string | null
      version_number: number
      is_active: boolean
      created_at: string
      categories: Array<{
        id: string
        name: string
        description: string | null
        weight: number
        pass_threshold: number
        level_definitions: Array<{
          level: string
          min_score: number
          max_score: number
          description: string
        }>
        mappings: Array<{
          id: string
          target_type: string
          target_id: string
          contribution_weight: number
          required_flag: boolean
        }>
      }>
    }>>(`/api/rubrics${query ? `?${query}` : ''}`)
  }

  async createRubric(data: {
    policy_template_id?: string | null
    flow_version_id: string
    name: string
    description?: string
    categories?: Array<{
      name: string
      description?: string
      weight: number
      pass_threshold: number
      level_definitions?: Array<{
        level: string
        min_score: number
        max_score: number
        description: string
      }>
    }>
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      is_active: boolean
    }>('/api/rubrics', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateRubric(rubricId: string, data: {
    name?: string
    description?: string
    is_active?: boolean
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      is_active: boolean
    }>(`/api/rubrics/${rubricId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteRubric(rubricId: string) {
    return this.request<{ message: string }>(`/api/rubrics/${rubricId}`, {
      method: 'DELETE',
    })
  }

  async createRubricCategory(rubricId: string, data: {
    name: string
    description?: string
    weight: number
    pass_threshold: number
    level_definitions?: Array<{
      level: string
      min_score: number
      max_score: number
      description: string
    }>
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      weight: number
      pass_threshold: number
      level_definitions: Array<any>
    }>(`/api/rubrics/${rubricId}/categories`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateRubricCategory(rubricId: string, categoryId: string, data: {
    name?: string
    description?: string
    weight?: number
    pass_threshold?: number
    level_definitions?: Array<{
      level: string
      min_score: number
      max_score: number
      description: string
    }>
  }) {
    return this.request<{
      id: string
      name: string
      description: string | null
      weight: number
      pass_threshold: number
      level_definitions: Array<any>
    }>(`/api/rubrics/${rubricId}/categories/${categoryId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteRubricCategory(rubricId: string, categoryId: string) {
    return this.request<{ message: string }>(`/api/rubrics/${rubricId}/categories/${categoryId}`, {
      method: 'DELETE',
    })
  }

  async createRubricMapping(rubricId: string, categoryId: string, data: {
    target_type: string
    target_id: string
    contribution_weight: number
    required_flag: boolean
  }) {
    return this.request<{
      id: string
      target_type: string
      target_id: string
      contribution_weight: number
      required_flag: boolean
    }>(`/api/rubrics/${rubricId}/categories/${categoryId}/mappings`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async deleteRubricMapping(rubricId: string, categoryId: string, mappingId: string) {
    return this.request<{ message: string }>(`/api/rubrics/${rubricId}/categories/${categoryId}/mappings/${mappingId}`, {
      method: 'DELETE',
    })
  }

  async publishRubric(rubricId: string) {
    return this.request<{ message: string }>(`/api/rubrics/${rubricId}/publish`, {
      method: 'POST',
    })
  }

  // Generic HTTP methods
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'GET',
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    })
  }
}

export const api = new ApiClient(API_URL)

