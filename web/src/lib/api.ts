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

    // Cloud Run has a 32MB limit, so for files > 30MB, use signed URL method automatically
    // This is transparent to the user - they just upload normally
    const FILE_SIZE_LIMIT = 30 * 1024 * 1024 // 30MB in bytes
    
    if (file.size > FILE_SIZE_LIMIT) {
      // Use signed URL method for large files
      try {
        // Step 1: Get signed URL from backend
        const { signed_url, file_url } = await this.getSignedUploadUrl(file.name)
        
        // Step 2: Upload directly to GCP Storage using signed URL
        await this.uploadFileToStorage(signed_url, file)
        
        // Step 3: Register the file with the backend
        return await this.uploadRecording(file.name, file_url)
      } catch (error: any) {
        throw new Error(error.message || 'Failed to upload large file using signed URL method')
      }
    }

    // For smaller files, try direct upload first
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
      
      // If we get a 413 error (Content Too Large), automatically fallback to signed URL method
      if (response.status === 413) {
        try {
          // Fallback to signed URL method
          const { signed_url, file_url } = await this.getSignedUploadUrl(file.name)
          await this.uploadFileToStorage(signed_url, file)
          return await this.uploadRecording(file.name, file_url)
        } catch (fallbackError: any) {
          throw new Error(fallbackError.message || 'Upload failed. File may be too large.')
        }
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
      policy_template_id: string
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
      policy_violations: Array<{
        id: string
        violation_type: string
        description: string
        severity: string
        criteria_id: string
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

  // Policy Template endpoints
  async getTemplates() {
    return this.request<
      Array<{
        id: string
        company_id: string
        template_name: string
        description: string | null
        is_active: boolean
        created_at: string
        criteria: Array<{
          id: string
          category_name: string
          weight: number
          passing_score: number
          evaluation_prompt: string
          created_at: string
        }>
      }>
    >('/api/templates')
  }

  async createTemplate(data: {
    template_name: string
    description?: string
    is_active?: boolean
    criteria: Array<{
      category_name: string
      weight: number
      passing_score: number
      evaluation_prompt: string
    }>
  }) {
    return this.request<{
      id: string
      company_id: string
      template_name: string
      description: string | null
      is_active: boolean
      created_at: string
      criteria: Array<{
        id: string
        category_name: string
        weight: number
        passing_score: number
        evaluation_prompt: string
        created_at: string
      }>
    }>('/api/templates', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateTemplate(templateId: string, data: {
    template_name: string
    description?: string
    is_active?: boolean
    criteria: Array<{
      category_name: string
      weight: number
      passing_score: number
      evaluation_prompt: string
    }>
  }) {
    return this.request<{
      id: string
      company_id: string
      template_name: string
      description: string | null
      is_active: boolean
      created_at: string
      criteria: Array<{
        id: string
        category_name: string
        weight: number
        passing_score: number
        evaluation_prompt: string
        created_at: string
      }>
    }>(`/api/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteTemplate(templateId: string) {
    return this.request<{ message: string }>(`/api/templates/${templateId}`, {
      method: 'DELETE',
    })
  }

  async addCriteria(templateId: string, data: {
    category_name: string
    weight: number
    passing_score: number
    evaluation_prompt: string
  }) {
    return this.request<{
      id: string
      category_name: string
      weight: number
      passing_score: number
      evaluation_prompt: string
      created_at: string
    }>(`/api/templates/${templateId}/criteria`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateCriteria(templateId: string, criteriaId: string, data: {
    category_name: string
    weight: number
    passing_score: number
    evaluation_prompt: string
  }) {
    return this.request<{
      id: string
      category_name: string
      weight: number
      passing_score: number
      evaluation_prompt: string
      created_at: string
    }>(`/api/templates/${templateId}/criteria/${criteriaId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteCriteria(templateId: string, criteriaId: string) {
    return this.request<{ message: string }>(`/api/templates/${templateId}/criteria/${criteriaId}`, {
      method: 'DELETE',
    })
  }

  async addRubricLevel(templateId: string, criteriaId: string, data: {
    level_name: string
    level_order: number
    min_score: number
    max_score: number
    description: string
    examples?: string
  }) {
    return this.request<{
      id: string
      criteria_id: string
      level_name: string
      level_order: number
      min_score: number
      max_score: number
      description: string
      examples: string | null
    }>(`/api/templates/${templateId}/criteria/${criteriaId}/rubric-levels`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateRubricLevel(templateId: string, criteriaId: string, levelId: string, data: {
    level_name: string
    level_order: number
    min_score: number
    max_score: number
    description: string
    examples?: string
  }) {
    return this.request<{
      id: string
      criteria_id: string
      level_name: string
      level_order: number
      min_score: number
      max_score: number
      description: string
      examples: string | null
    }>(`/api/templates/${templateId}/criteria/${criteriaId}/rubric-levels/${levelId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteRubricLevel(templateId: string, criteriaId: string, levelId: string) {
    return this.request<{ message: string }>(`/api/templates/${templateId}/criteria/${criteriaId}/rubric-levels/${levelId}`, {
      method: 'DELETE',
    })
  }

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
      policy_template_id: string
      overall_score: number
      resolution_detected: boolean
      resolution_confidence: number
      llm_analysis: any
      status: string
      created_at: string
      category_scores: Array<{
        id: string
        category_name: string
        score: number
        feedback: string | null
      }>
      policy_violations: Array<{
        id: string
        violation_type: string
        description: string
        severity: string
        criteria_id: string
      }>
      template: {
        id: string
        template_name: string
        description: string | null
        criteria: Array<{
          id: string
          category_name: string
          weight: number
          passing_score: number
          evaluation_prompt: string
          rubric_levels: Array<{
            id: string
            level_name: string
            level_order: number
            min_score: number
            max_score: number
            description: string
            examples: string | null
          }>
        }>
      }
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
}

export const api = new ApiClient(API_URL)

