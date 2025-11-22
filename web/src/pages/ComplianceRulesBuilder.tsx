import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle, FaSpinner, FaToggleOn, FaToggleOff } from 'react-icons/fa'
import { ConfirmModal } from '@/components/modals'

interface FlowVersion {
  id: string
  name: string
  stages: Array<{
    id: string
    name: string
    steps: Array<{
      id: string
      name: string
    }>
  }>
}

interface ComplianceRule {
  id: string
  flow_version_id: string
  title: string
  description: string | null
  severity: 'critical' | 'major' | 'minor'
  rule_type: 'required_phrase' | 'forbidden_phrase' | 'sequence_rule' | 'timing_rule' | 'verification_rule' | 'conditional_rule'
  applies_to_stages: string[]
  params: any
  active: boolean
  created_at: string
}

export function ComplianceRulesBuilder() {
  const [flowVersions, setFlowVersions] = useState<FlowVersion[]>([])
  const [selectedFlowVersion, setSelectedFlowVersion] = useState<FlowVersion | null>(null)
  const [rules, setRules] = useState<ComplianceRule[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRuleModal, setShowRuleModal] = useState(false)
  const [editingRule, setEditingRule] = useState<ComplianceRule | null>(null)
  const [rulePreview, setRulePreview] = useState<string>('')

  // Form state
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [severity, setSeverity] = useState<'critical' | 'major' | 'minor'>('major')
  const [ruleType, setRuleType] = useState<ComplianceRule['rule_type']>('required_phrase')
  const [appliesToStages, setAppliesToStages] = useState<string[]>([])
  const [params, setParams] = useState<any>({})

  useEffect(() => {
    loadFlowVersions()
  }, [])

  useEffect(() => {
    if (selectedFlowVersion) {
      loadRules()
    }
  }, [selectedFlowVersion])

  useEffect(() => {
    generatePreview()
  }, [title, description, severity, ruleType, appliesToStages, params, selectedFlowVersion])

  const loadFlowVersions = async () => {
    try {
      setLoading(true)
      const versions = await api.listFlowVersions()
      setFlowVersions(versions as any)
      if (versions.length > 0) {
        setSelectedFlowVersion(versions[0] as any)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load flow versions')
    } finally {
      setLoading(false)
    }
  }

  const loadRules = async () => {
    if (!selectedFlowVersion) return
    try {
      setLoading(true)
      const rulesData = await api.listComplianceRules({ flow_version_id: selectedFlowVersion.id })
      setRules(rulesData as any)
    } catch (err: any) {
      setError(err.message || 'Failed to load compliance rules')
    } finally {
      setLoading(false)
    }
  }

  const generatePreview = () => {
    if (!selectedFlowVersion || !title || !ruleType) {
      setRulePreview('')
      return
    }

    let preview = ''
    const stageNames = appliesToStages
      .map(id => selectedFlowVersion.stages.find(s => s.id === id)?.name)
      .filter(Boolean)
      .join(', ')

    switch (ruleType) {
      case 'required_phrase':
        const phrases = params.phrases || []
        preview = `Required: agent must say one of [${phrases.join(', ')}]${stageNames ? ` in ${stageNames} stage(s)` : ' anywhere in call'}.`
        break
      case 'forbidden_phrase':
        const forbiddenPhrases = params.phrases || []
        preview = `Forbidden: agent must not say phrases matching [${forbiddenPhrases.join(', ')}]${stageNames ? ` in ${stageNames} stage(s)` : ' anywhere in call'}.`
        break
      case 'sequence_rule':
        const beforeStep = selectedFlowVersion.stages
          .flatMap(s => s.steps)
          .find(s => s.id === params.before_step_id)
        const afterStep = selectedFlowVersion.stages
          .flatMap(s => s.steps)
          .find(s => s.id === params.after_step_id)
        preview = `Sequence: ${beforeStep?.name || 'Step A'} must occur before ${afterStep?.name || 'Step B'}.`
        break
      case 'timing_rule':
        const target = params.target === 'step'
          ? selectedFlowVersion.stages.flatMap(s => s.steps).find(s => s.id === params.target_id_or_phrase)?.name
          : params.target_id_or_phrase
        preview = `${target} must occur within ${params.within_seconds || 0} seconds of ${params.reference === 'call_start' ? 'call start' : 'previous step'}.`
        break
      case 'verification_rule':
        const verifStep = selectedFlowVersion.stages
          .flatMap(s => s.steps)
          .find(s => s.id === params.verification_step_id)
        const beforeStep2 = selectedFlowVersion.stages
          .flatMap(s => s.steps)
          .find(s => s.id === params.must_complete_before_step_id)
        preview = `Verification: ${verifStep?.name || 'Verification step'} must complete ${params.required_question_count || 0} questions before ${beforeStep2?.name || 'target step'}.`
        break
      case 'conditional_rule':
        preview = `Conditional: If ${params.condition?.type || 'condition'} is ${params.condition?.value || 'value'}, then required actions must occur.`
        break
    }

    setRulePreview(preview)
  }

  const handleCreateRule = () => {
    setEditingRule(null)
    setTitle('')
    setDescription('')
    setSeverity('major')
    setRuleType('required_phrase')
    setAppliesToStages([])
    setParams({})
    setShowRuleModal(true)
  }

  const handleEditRule = (rule: ComplianceRule) => {
    setEditingRule(rule)
    setTitle(rule.title)
    setDescription(rule.description || '')
    setSeverity(rule.severity)
    setRuleType(rule.rule_type)
    setAppliesToStages(rule.applies_to_stages || [])
    setParams(rule.params || {})
    setShowRuleModal(true)
  }

  const handleSaveRule = async () => {
    if (!selectedFlowVersion || !title.trim()) {
      setError('Title is required')
      return
    }

    try {
      setSaving(true)
      setError(null)

      // Ensure params has required fields based on rule type
      let validatedParams = { ...params }
      
      // Validate required_phrase or forbidden_phrase
      if (ruleType === 'required_phrase' || ruleType === 'forbidden_phrase') {
        if (!validatedParams.phrases || !Array.isArray(validatedParams.phrases) || validatedParams.phrases.length === 0) {
          setError('At least one phrase is required')
          setSaving(false)
          return
        }
        // Set defaults
        validatedParams.match_type = validatedParams.match_type || 'contains'
        validatedParams.case_sensitive = validatedParams.case_sensitive || false
        validatedParams.scope = validatedParams.scope || 'call'
      }
      
      // Validate sequence_rule
      if (ruleType === 'sequence_rule') {
        if (!validatedParams.before_step_id || !validatedParams.after_step_id) {
          setError('Both before and after steps are required')
          setSaving(false)
          return
        }
      }
      
      // Validate timing_rule
      if (ruleType === 'timing_rule') {
        if (!validatedParams.within_seconds || validatedParams.within_seconds <= 0) {
          setError('Within seconds must be a positive number')
          setSaving(false)
          return
        }
        validatedParams.target = validatedParams.target || 'step'
        validatedParams.reference = validatedParams.reference || 'call_start'
      }
      
      // Validate verification_rule
      if (ruleType === 'verification_rule') {
        if (!validatedParams.verification_step_id || !validatedParams.must_complete_before_step_id) {
          setError('Verification step and completion step are required')
          setSaving(false)
          return
        }
        validatedParams.required_question_count = validatedParams.required_question_count || 1
      }
      
      // Validate conditional_rule
      if (ruleType === 'conditional_rule') {
        if (!validatedParams.condition || !validatedParams.required_actions || !Array.isArray(validatedParams.required_actions) || validatedParams.required_actions.length === 0) {
          setError('Condition and at least one required action are needed')
          setSaving(false)
          return
        }
      }

      const ruleData = {
        flow_version_id: selectedFlowVersion.id,
        title: title.trim(),
        description: description.trim() || title.trim(), // Use title as fallback if description is empty
        severity,
        rule_type: ruleType,
        applies_to_stages: appliesToStages.length > 0 ? appliesToStages : [],
        params: validatedParams,
        active: true,
      }

      if (editingRule) {
        await api.updateComplianceRule(editingRule.id, ruleData)
      } else {
        await api.createComplianceRule(ruleData)
      }

      await loadRules()
      setShowRuleModal(false)
      resetForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save rule')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRule = (rule: ComplianceRule) => {
    setDeleteConfirmModal({ isOpen: true, rule })
  }

  const confirmDeleteRule = async () => {
    if (!deleteConfirmModal) return
    const rule = deleteConfirmModal.rule

    try {
      setSaving(true)
      await api.deleteComplianceRule(rule.id)
      await loadRules()
      setDeleteConfirmModal(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete rule')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleRule = async (rule: ComplianceRule) => {
    try {
      await api.toggleComplianceRule(rule.id)
      await loadRules()
    } catch (err: any) {
      setError(err.message || 'Failed to toggle rule')
    }
  }

  const resetForm = () => {
    setEditingRule(null)
    setTitle('')
    setDescription('')
    setSeverity('major')
    setRuleType('required_phrase')
    setAppliesToStages([])
    setParams({})
  }

  const updateParams = (key: string, value: any) => {
    setParams((prev: any) => ({ ...prev, [key]: value }))
  }

  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
      case 'major': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400'
      case 'minor': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  if (loading && flowVersions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading Compliance Rules Builder...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">
                Compliance Rules Builder
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Define deterministic compliance rules for quality evaluation
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedFlowVersion?.id || ''}
                onChange={(e) => {
                  const fv = flowVersions.find(v => v.id === e.target.value)
                  setSelectedFlowVersion(fv || null)
                }}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                {flowVersions.map(fv => (
                  <option key={fv.id} value={fv.id}>
                    {fv.name}
                  </option>
                ))}
              </select>
              {selectedFlowVersion && (
                <button
                  onClick={handleCreateRule}
                  className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 flex items-center gap-2"
                >
                  <FaPlus className="w-4 h-4" />
                  Add Rule
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-center gap-3">
            <FaExclamationCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
            <span className="text-sm text-red-800 dark:text-red-200 flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-red-600 dark:text-red-400">
              <FaTimes className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Rules List */}
        {selectedFlowVersion && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Compliance Rules ({rules.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {rules.length === 0 ? (
                <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                  No compliance rules defined. Click "Add Rule" to create one.
                </div>
              ) : (
                rules.map(rule => (
                  <div key={rule.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-base font-medium text-gray-900 dark:text-white">
                            {rule.title}
                          </h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(rule.severity)}`}>
                            {rule.severity}
                          </span>
                          <span className="px-2 py-1 text-xs font-medium rounded bg-brand-100 text-brand-800 dark:bg-brand-900/20 dark:text-brand-400">
                            {rule.rule_type.replace('_', ' ')}
                          </span>
                        </div>
                        {rule.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {rule.description}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                          {rule.applies_to_stages.length > 0
                            ? `Applies to: ${rule.applies_to_stages.length} stage(s)`
                            : 'Applies to: entire call'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleRule(rule)}
                          className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          title={rule.active ? 'Deactivate' : 'Activate'}
                        >
                          {rule.active ? (
                            <FaToggleOn className="w-5 h-5 text-green-500" />
                          ) : (
                            <FaToggleOff className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEditRule(rule)}
                          className="p-2 text-gray-400 hover:text-brand-600 dark:hover:text-brand-400"
                          title="Edit"
                        >
                          <FaEdit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule)}
                          className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="Delete"
                        >
                          <FaTrash className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Rule Editor Modal */}
        {showRuleModal && selectedFlowVersion && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full my-8">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {editingRule ? 'Edit Compliance Rule' : 'Create Compliance Rule'}
                </h2>
              </div>
              <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                {/* Basic Fields */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g., Recording Disclosure Required"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Human-readable description of the rule"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Severity <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={severity}
                      onChange={(e) => setSeverity(e.target.value as any)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="critical">Critical</option>
                      <option value="major">Major</option>
                      <option value="minor">Minor</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Rule Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={ruleType}
                      onChange={(e) => {
                        setRuleType(e.target.value as any)
                        setParams({})
                      }}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="required_phrase">Required Phrase</option>
                      <option value="forbidden_phrase">Forbidden Phrase</option>
                      <option value="sequence_rule">Sequence Rule</option>
                      <option value="timing_rule">Timing Rule</option>
                      <option value="verification_rule">Verification Rule</option>
                      <option value="conditional_rule">Conditional Rule</option>
                    </select>
                  </div>
                </div>

                {/* Applies to Stages */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Applies to Stages (optional - leave empty for call-wide)
                  </label>
                  <select
                    multiple
                    value={appliesToStages}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value)
                      setAppliesToStages(selected)
                    }}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white min-h-[100px]"
                  >
                    {selectedFlowVersion.stages.map(stage => (
                      <option key={stage.id} value={stage.id}>
                        {stage.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Hold Ctrl/Cmd to select multiple stages
                  </p>
                </div>

                {/* Rule Type Specific Params */}
                {(ruleType === 'required_phrase' || ruleType === 'forbidden_phrase') && (
                  <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Phrases <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        value={(params.phrases || []).join('\n')}
                        onChange={(e) => {
                          const phrases = e.target.value.split('\n').filter(p => p.trim())
                          updateParams('phrases', phrases)
                        }}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="One phrase per line"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Match Type
                        </label>
                        <select
                          value={params.match_type || 'contains'}
                          onChange={(e) => updateParams('match_type', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="contains">Contains</option>
                          <option value="exact">Exact</option>
                          <option value="regex">Regex</option>
                        </select>
                      </div>
                      <div className="flex items-center pt-6">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={params.case_sensitive || false}
                            onChange={(e) => updateParams('case_sensitive', e.target.checked)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm text-gray-700 dark:text-gray-300">Case Sensitive</span>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {ruleType === 'sequence_rule' && (
                  <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Before Step <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={params.before_step_id || ''}
                        onChange={(e) => updateParams('before_step_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="">Select step...</option>
                        {selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                          <option key={step.id} value={step.id}>
                            {step.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        After Step <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={params.after_step_id || ''}
                        onChange={(e) => updateParams('after_step_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="">Select step...</option>
                        {selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                          <option key={step.id} value={step.id}>
                            {step.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {ruleType === 'timing_rule' && (
                  <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Target Type
                      </label>
                      <select
                        value={params.target || 'step'}
                        onChange={(e) => {
                          updateParams('target', e.target.value)
                          updateParams('target_id_or_phrase', '')
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="step">Step</option>
                        <option value="phrase">Phrase</option>
                      </select>
                    </div>
                    {params.target === 'step' ? (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Target Step
                        </label>
                        <select
                          value={params.target_id_or_phrase || ''}
                          onChange={(e) => updateParams('target_id_or_phrase', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="">Select step...</option>
                          {selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                            <option key={step.id} value={step.id}>
                              {step.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Target Phrase
                        </label>
                        <input
                          type="text"
                          value={params.target_id_or_phrase || ''}
                          onChange={(e) => updateParams('target_id_or_phrase', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Within Seconds <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="number"
                          value={params.within_seconds || ''}
                          onChange={(e) => updateParams('within_seconds', parseFloat(e.target.value) || 0)}
                          min="0"
                          step="0.1"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Reference
                        </label>
                        <select
                          value={params.reference || 'call_start'}
                          onChange={(e) => updateParams('reference', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="call_start">Call Start</option>
                          <option value="previous_step">Previous Step</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {ruleType === 'verification_rule' && (
                  <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Verification Step <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={params.verification_step_id || ''}
                        onChange={(e) => updateParams('verification_step_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="">Select step...</option>
                        {selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                          <option key={step.id} value={step.id}>
                            {step.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Required Question Count <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        value={params.required_question_count || ''}
                        onChange={(e) => updateParams('required_question_count', parseInt(e.target.value) || 0)}
                        min="1"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Must Complete Before Step
                      </label>
                      <select
                        value={params.must_complete_before_step_id || ''}
                        onChange={(e) => updateParams('must_complete_before_step_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="">Select step...</option>
                        {selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                          <option key={step.id} value={step.id}>
                            {step.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {ruleType === 'conditional_rule' && (
                  <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Condition Type
                      </label>
                      <select
                        value={params.condition?.type || 'sentiment'}
                        onChange={(e) => updateParams('condition', { ...params.condition, type: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="sentiment">Sentiment</option>
                        <option value="phrase_mentioned">Phrase Mentioned</option>
                        <option value="metadata_flag">Metadata Flag</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Operator
                        </label>
                        <select
                          value={params.condition?.operator || 'equals'}
                          onChange={(e) => updateParams('condition', { ...params.condition, operator: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="equals">Equals</option>
                          <option value="contains">Contains</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Value
                        </label>
                        <input
                          type="text"
                          value={params.condition?.value || ''}
                          onChange={(e) => updateParams('condition', { ...params.condition, value: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Rule Preview */}
                {rulePreview && (
                  <div className="p-4 bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800 rounded-md">
                    <p className="text-sm font-medium text-brand-900 dark:text-brand-200 mb-1">Rule Preview:</p>
                    <p className="text-sm text-brand-800 dark:text-brand-300">{rulePreview}</p>
                  </div>
                )}
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowRuleModal(false)
                    resetForm()
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveRule}
                  disabled={saving || !title.trim()}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSave className="w-4 h-4" />}
                  Save Rule
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

