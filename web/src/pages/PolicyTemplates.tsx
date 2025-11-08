import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle, FaSpinner, FaFileAlt, FaChartBar, FaBullseye, FaRuler, FaLightbulb, FaCheckCircle, FaChevronDown, FaChevronRight } from 'react-icons/fa'

interface RubricLevel {
  id: string
  criteria_id: string
  level_name: string
  level_order: number
  min_score: number
  max_score: number
  description: string
  examples: string | null
}

interface EvaluationCriteria {
  id: string
  category_name: string
  weight: number
  passing_score: number
  evaluation_prompt: string
  created_at?: string
  rubric_levels?: RubricLevel[]
}

interface PolicyTemplate {
  id: string
  company_id: string
  template_name: string
  description: string | null
  is_active: boolean
  created_at: string
  criteria: EvaluationCriteria[]
}

export function PolicyTemplates() {
  const [templates, setTemplates] = useState<PolicyTemplate[]>([])
  const [activeTemplate, setActiveTemplate] = useState<PolicyTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<string | null>(null)
  const [editingCriteria, setEditingCriteria] = useState<string | null>(null)
  const [editingRubricLevel, setEditingRubricLevel] = useState<string | null>(null)
  const [expandedCriteria, setExpandedCriteria] = useState<Set<string>>(new Set())
  const [newTemplateName, setNewTemplateName] = useState('')
  const [newTemplateDesc, setNewTemplateDesc] = useState('')
  const [showNewTemplate, setShowNewTemplate] = useState(false)
  const [saving, setSaving] = useState(false)

  // Fetch templates from backend
  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getTemplates()
      setTemplates(data)
      
      // Set first active template as active, or first template if none active
      const active = data.find(t => t.is_active) || data[0] || null
      setActiveTemplate(active)
    } catch (err: any) {
      console.error('Failed to load templates:', err)
      setError(err.message || 'Failed to load templates. Please log in.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTemplate = async () => {
    if (!newTemplateName.trim()) return

    try {
      setSaving(true)
      setError(null)
      const newTemplate = await api.createTemplate({
        template_name: newTemplateName,
        description: newTemplateDesc || undefined,
        is_active: false,
        criteria: []
      })
      
      setTemplates(prev => [...prev, newTemplate])
      setNewTemplateName('')
      setNewTemplateDesc('')
      setShowNewTemplate(false)
    } catch (err: any) {
      setError(err.message || 'Failed to create template')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateTemplate = async (templateId: string, updates: Partial<PolicyTemplate>) => {
    const template = templates.find(t => t.id === templateId)
    if (!template) return

    try {
      setSaving(true)
      setError(null)
      const updated = await api.updateTemplate(templateId, {
        template_name: updates.template_name || template.template_name,
        description: updates.description || template.description || undefined,
        is_active: updates.is_active !== undefined ? updates.is_active : template.is_active,
        criteria: template.criteria.map(c => ({
          category_name: c.category_name,
          weight: c.weight,
          passing_score: c.passing_score,
          evaluation_prompt: c.evaluation_prompt
        }))
      })
      
      setTemplates(prev => prev.map(t => t.id === templateId ? updated : t))
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(updated)
      }
      setEditingTemplate(null)
    } catch (err: any) {
      setError(err.message || 'Failed to update template')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm('Delete this template? This action cannot be undone.')) return

    try {
      setSaving(true)
      setError(null)
      await api.deleteTemplate(templateId)
      setTemplates(prev => prev.filter(t => t.id !== templateId))
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(null)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete template')
    } finally {
      setSaving(false)
    }
  }

  const handleSetActive = async (templateId: string) => {
    const template = templates.find(t => t.id === templateId)
    if (!template) return

    try {
      setSaving(true)
      setError(null)
      
      // Deactivate all other templates
      const updates = templates.map(t => ({
        ...t,
        is_active: t.id === templateId
      }))

      // Update each template's active status
      for (const t of templates) {
        if (t.id === templateId) {
          await api.updateTemplate(t.id, {
            template_name: t.template_name,
            description: t.description || undefined,
            is_active: true,
            criteria: t.criteria.map(c => ({
              category_name: c.category_name,
              weight: c.weight,
              passing_score: c.passing_score,
              evaluation_prompt: c.evaluation_prompt
            }))
          })
        } else if (t.is_active) {
          await api.updateTemplate(t.id, {
            template_name: t.template_name,
            description: t.description || undefined,
            is_active: false,
            criteria: t.criteria.map(c => ({
              category_name: c.category_name,
              weight: c.weight,
              passing_score: c.passing_score,
              evaluation_prompt: c.evaluation_prompt
            }))
          })
        }
      }

      // Reload templates to get updated state
      await loadTemplates()
    } catch (err: any) {
      setError(err.message || 'Failed to set active template')
    } finally {
      setSaving(false)
    }
  }

  const handleAddCriteria = async (templateId: string, criteria: Omit<EvaluationCriteria, 'id' | 'created_at'>) => {
    try {
      setSaving(true)
      setError(null)
      const newCriteria = await api.addCriteria(templateId, {
        category_name: criteria.category_name,
        weight: criteria.weight,
        passing_score: criteria.passing_score,
        evaluation_prompt: criteria.evaluation_prompt
      })
      
      setTemplates(prev => prev.map(t => 
        t.id === templateId 
          ? { ...t, criteria: [...t.criteria, newCriteria] }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? { ...prev, criteria: [...prev.criteria, newCriteria] } : null)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add criteria')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateCriteria = async (templateId: string, criteriaId: string, updates: Partial<EvaluationCriteria>) => {
    const template = templates.find(t => t.id === templateId)
    if (!template) return

    const criteria = template.criteria.find(c => c.id === criteriaId)
    if (!criteria) return

    try {
      setSaving(true)
      setError(null)
      
      // Use the new update criteria endpoint
      const updatedCriteria = await api.updateCriteria(templateId, criteriaId, {
        category_name: updates.category_name || criteria.category_name,
        weight: updates.weight !== undefined ? updates.weight : criteria.weight,
        passing_score: updates.passing_score !== undefined ? updates.passing_score : criteria.passing_score,
        evaluation_prompt: updates.evaluation_prompt || criteria.evaluation_prompt
      })
      
      // Update templates and active template
      setTemplates(prev => prev.map(t => 
        t.id === templateId
          ? { ...t, criteria: t.criteria.map(c => c.id === criteriaId ? updatedCriteria : c) }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? {
          ...prev,
          criteria: prev.criteria.map(c => c.id === criteriaId ? updatedCriteria : c)
        } : null)
      }
      
      setEditingCriteria(null)
    } catch (err: any) {
      setError(err.message || 'Failed to update criteria')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteCriteria = async (templateId: string, criteriaId: string) => {
    if (!confirm('Are you sure you want to delete this criteria? This action cannot be undone.')) return

    try {
      setSaving(true)
      setError(null)
      
      // Use the new delete criteria endpoint
      await api.deleteCriteria(templateId, criteriaId)
      
      // Update templates and active template
      setTemplates(prev => prev.map(t => 
        t.id === templateId
          ? { ...t, criteria: t.criteria.filter(c => c.id !== criteriaId) }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? {
          ...prev,
          criteria: prev.criteria.filter(c => c.id !== criteriaId)
        } : null)
      }
      
      // Remove from expanded set
      setExpandedCriteria(prev => {
        const newSet = new Set(prev)
        newSet.delete(criteriaId)
        return newSet
      })
    } catch (err: any) {
      setError(err.message || 'Failed to delete criteria')
    } finally {
      setSaving(false)
    }
  }

  const handleAddRubricLevel = async (templateId: string, criteriaId: string, level: Omit<RubricLevel, 'id' | 'criteria_id'>) => {
    try {
      setSaving(true)
      setError(null)
      
      const newLevel = await api.addRubricLevel(templateId, criteriaId, {
        level_name: level.level_name,
        level_order: level.level_order,
        min_score: level.min_score,
        max_score: level.max_score,
        description: level.description,
        examples: level.examples || undefined
      })
      
      // Update templates
      setTemplates(prev => prev.map(t => 
        t.id === templateId
          ? {
              ...t,
              criteria: t.criteria.map(c => 
                c.id === criteriaId
                  ? { ...c, rubric_levels: [...(c.rubric_levels || []), newLevel] }
                  : c
              )
            }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? {
          ...prev,
          criteria: prev.criteria.map(c => 
            c.id === criteriaId
              ? { ...c, rubric_levels: [...(c.rubric_levels || []), newLevel] }
              : c
          )
        } : null)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add rubric level')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateRubricLevel = async (templateId: string, criteriaId: string, levelId: string, updates: Partial<RubricLevel>) => {
    try {
      setSaving(true)
      setError(null)
      
      const level = activeTemplate?.criteria.find(c => c.id === criteriaId)?.rubric_levels?.find(l => l.id === levelId)
      if (!level) return
      
      const updatedLevel = await api.updateRubricLevel(templateId, criteriaId, levelId, {
        level_name: updates.level_name || level.level_name,
        level_order: updates.level_order !== undefined ? updates.level_order : level.level_order,
        min_score: updates.min_score !== undefined ? updates.min_score : level.min_score,
        max_score: updates.max_score !== undefined ? updates.max_score : level.max_score,
        description: updates.description || level.description,
        examples: updates.examples !== undefined ? updates.examples : level.examples || undefined
      })
      
      // Update templates
      setTemplates(prev => prev.map(t => 
        t.id === templateId
          ? {
              ...t,
              criteria: t.criteria.map(c => 
                c.id === criteriaId
                  ? {
                      ...c,
                      rubric_levels: (c.rubric_levels || []).map(l => l.id === levelId ? updatedLevel : l)
                    }
                  : c
              )
            }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? {
          ...prev,
          criteria: prev.criteria.map(c => 
            c.id === criteriaId
              ? {
                  ...c,
                  rubric_levels: (c.rubric_levels || []).map(l => l.id === levelId ? updatedLevel : l)
                }
              : c
          )
        } : null)
      }
      
      setEditingRubricLevel(null)
    } catch (err: any) {
      setError(err.message || 'Failed to update rubric level')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRubricLevel = async (templateId: string, criteriaId: string, levelId: string) => {
    if (!confirm('Delete this rubric level?')) return

    try {
      setSaving(true)
      setError(null)
      
      await api.deleteRubricLevel(templateId, criteriaId, levelId)
      
      // Update templates
      setTemplates(prev => prev.map(t => 
        t.id === templateId
          ? {
              ...t,
              criteria: t.criteria.map(c => 
                c.id === criteriaId
                  ? {
                      ...c,
                      rubric_levels: (c.rubric_levels || []).filter(l => l.id !== levelId)
                    }
                  : c
              )
            }
          : t
      ))
      
      if (activeTemplate?.id === templateId) {
        setActiveTemplate(prev => prev ? {
          ...prev,
          criteria: prev.criteria.map(c => 
            c.id === criteriaId
              ? {
                  ...c,
                  rubric_levels: (c.rubric_levels || []).filter(l => l.id !== levelId)
                }
              : c
          )
        } : null)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete rubric level')
    } finally {
      setSaving(false)
    }
  }

  const toggleCriteriaExpanded = (criteriaId: string) => {
    setExpandedCriteria(prev => {
      const newSet = new Set(prev)
      if (newSet.has(criteriaId)) {
        newSet.delete(criteriaId)
      } else {
        newSet.add(criteriaId)
      }
      return newSet
    })
  }

  const totalWeight = (criteria: EvaluationCriteria[]): number => {
    if (!criteria || criteria.length === 0) return 0
    const sum = criteria.reduce((acc, c) => {
      const weight = typeof c.weight === 'number' ? c.weight : parseFloat(String(c.weight || 0))
      return acc + (isNaN(weight) ? 0 : weight)
    }, 0)
    return Number(sum) || 0
  }

  const validateWeight = (criteria: EvaluationCriteria[]) => {
    const total = totalWeight(criteria)
    return Math.abs(total - 100) < 0.01
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading templates...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900 py-8">
      {/* Enhanced background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -right-40 w-[750px] h-[750px] bg-brand-400/11 dark:bg-brand-500/5.5 rounded-full blur-[110px]"></div>
        <div className="absolute top-1/2 -left-40 w-[650px] h-[650px] bg-blue-400/9 dark:bg-blue-500/4.5 rounded-full blur-[95px]"></div>
        <div className="absolute bottom-0 right-1/3 w-[600px] h-[600px] bg-purple-400/8 dark:bg-purple-500/4 rounded-full blur-[90px]"></div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
        {/* Header Section with improved styling */}
        <div className="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center space-x-3">
                <FaFileAlt className="w-8 h-8 text-brand-500" />
                <span>Policy Templates</span>
              </h1>
              <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
                Create and manage evaluation criteria with customizable rubric levels for consistent, objective quality assurance. Define performance levels (Excellent, Good, Average, etc.) for each category.
              </p>
            </div>
            <div className="flex items-center space-x-3 flex-shrink-0">
              <button
                onClick={loadTemplates}
                disabled={loading}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center space-x-2 transition-colors disabled:opacity-50 shadow-sm"
                title="Refresh templates"
              >
                <FaSpinner className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
              <button
                onClick={() => setShowNewTemplate(true)}
                disabled={saving || showNewTemplate}
                className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 flex items-center space-x-2 shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <FaPlus className="w-4 h-4" />
                <span>New Template</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 dark:border-red-400 rounded-lg shadow-sm flex items-center space-x-3 animate-fade-in">
            <FaExclamationCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
            <span className="text-sm text-red-800 dark:text-red-200 flex-1">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
            >
              <FaTimes className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* New Template Form */}
        {showNewTemplate && (
          <div className="mb-6 bg-white dark:bg-gray-800 rounded-xl border-2 border-brand-200 dark:border-brand-800 shadow-lg p-6 animate-slide-down">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                <FaPlus className="w-5 h-5 text-brand-500" />
                <span>Create New Template</span>
              </h2>
              <button
                onClick={() => {
                  setShowNewTemplate(false)
                  setNewTemplateName('')
                  setNewTemplateDesc('')
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <FaTimes className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Template Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTemplateName}
                  onChange={(e) => setNewTemplateName(e.target.value)}
                  placeholder="e.g., Customer Service QA, Sales Call Evaluation"
                  className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-brand-500 focus:ring-2 focus:ring-brand-200 dark:focus:ring-brand-800 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={newTemplateDesc}
                  onChange={(e) => setNewTemplateDesc(e.target.value)}
                  placeholder="Describe what this template evaluates (e.g., 'Quality assurance for customer support calls focusing on compliance, empathy, and resolution')"
                  rows={3}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-brand-500 focus:ring-2 focus:ring-brand-200 dark:focus:ring-brand-800 transition-colors resize-none"
                />
              </div>
              <div className="flex space-x-3 pt-2">
                <button
                  onClick={handleCreateTemplate}
                  disabled={saving || !newTemplateName.trim()}
                  className="px-6 py-2.5 bg-brand-500 text-white rounded-lg hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-md hover:shadow-lg transition-all font-medium"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaCheck className="w-4 h-4" />}
                  <span>Create Template</span>
                </button>
                <button
                  onClick={() => {
                    setShowNewTemplate(false)
                    setNewTemplateName('')
                    setNewTemplateDesc('')
                  }}
                  disabled={saving}
                  className="px-6 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Templates List */}
        {templates.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No templates yet. Create your first template to get started.
            </p>
            <button
              onClick={() => setShowNewTemplate(true)}
              className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600"
            >
              Create Template
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {templates.map((template) => {
              const isActive = activeTemplate?.id === template.id
              const weightsValid = validateWeight(template.criteria)
              const isEditing = editingTemplate === template.id

              return (
                <div
                  key={template.id}
                  className={`bg-white dark:bg-gray-800 rounded-xl border-2 shadow-md hover:shadow-lg transition-all ${
                    isActive
                      ? 'border-brand-500 dark:border-brand-500 ring-2 ring-brand-200 dark:ring-brand-800'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  {/* Template Header */}
                  <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-transparent dark:from-gray-800/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {isEditing ? (
                          <div className="space-y-4">
                            <input
                              type="text"
                              value={template.template_name}
                              onChange={(e) =>
                                handleUpdateTemplate(template.id, { template_name: e.target.value })
                              }
                              className="text-xl font-semibold px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full"
                            />
                            <textarea
                              value={template.description || ''}
                              onChange={(e) =>
                                handleUpdateTemplate(template.id, { description: e.target.value })
                              }
                              rows={2}
                              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full"
                            />
                          </div>
                        ) : (
                          <div>
                            <div className="flex items-center space-x-3 mb-2">
                              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                {template.template_name}
                              </h2>
                              {isActive && (
                                <span className="px-3 py-1 bg-brand-500 text-white text-xs font-semibold rounded-full shadow-sm flex items-center space-x-1">
                                  <FaCheckCircle className="w-3 h-3" />
                                  <span>Active</span>
                                </span>
                              )}
                            </div>
                            <p className="text-gray-600 dark:text-gray-400">
                              {template.description || 'No description'}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {!isEditing && (
                          <>
                            <button
                              onClick={() => handleSetActive(template.id)}
                              disabled={saving}
                              className={`px-3 py-1.5 rounded-lg text-sm disabled:opacity-50 ${
                                isActive
                                  ? 'bg-brand-500 text-white'
                                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                              }`}
                            >
                              {isActive ? 'Active' : 'Set Active'}
                            </button>
                            <button
                              onClick={() => setEditingTemplate(template.id)}
                              disabled={saving}
                              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50"
                            >
                              <FaEdit className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        {isEditing && (
                          <button
                            onClick={() => setEditingTemplate(null)}
                            disabled={saving}
                            className="p-2 text-green-600 dark:text-green-400 disabled:opacity-50"
                          >
                            <FaSave className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteTemplate(template.id)}
                          disabled={saving}
                          className="p-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 disabled:opacity-50"
                        >
                          <FaTrash className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Criteria List */}
                  <div className="p-6 bg-gray-50/50 dark:bg-gray-900/30">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center space-x-2">
                          <FaChartBar className="w-5 h-5 text-brand-500" />
                          <span>Evaluation Criteria</span>
                          <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                            ({template.criteria.length} {template.criteria.length === 1 ? 'category' : 'categories'})
                          </span>
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Define evaluation categories with customizable rubric levels. Each category can have multiple performance levels (Excellent, Good, Average, etc.) with specific score ranges and descriptions.
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          // Calculate remaining weight for new category
                          const currentWeight = totalWeight(template.criteria)
                          const remainingWeight = 100 - currentWeight
                          const defaultWeight = Math.max(0, Math.min(remainingWeight, 33.33))
                          
                          handleAddCriteria(template.id, {
                            category_name: 'New Category',
                            weight: defaultWeight,
                            passing_score: 70,
                            evaluation_prompt: 'Evaluate this category based on the requirements...',
                          })
                        }}
                        disabled={saving || totalWeight(template.criteria) >= 100}
                        className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 flex items-center space-x-2 text-sm font-medium shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
                        title={totalWeight(template.criteria) >= 100 ? "Total weight already equals 100%" : "Add a new evaluation criteria"}
                      >
                        <FaPlus className="w-4 h-4" />
                        <span>Add Criteria</span>
                      </button>
                    </div>

                    {/* Weight Validation */}
                    {!weightsValid && template.criteria.length > 0 && (
                      <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500 dark:border-yellow-400 rounded-lg flex items-center space-x-3 shadow-sm">
                        <FaExclamationCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                            Weight Total Invalid
                          </p>
                          <p className="text-sm text-yellow-700 dark:text-yellow-300">
                            Total weight must equal 100%. Current: <span className="font-bold">{Number(totalWeight(template.criteria)).toFixed(1)}%</span>
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Weight Summary */}
                    {weightsValid && template.criteria.length > 0 && (
                      <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 dark:border-green-400 rounded-lg flex items-center space-x-2">
                        <FaCheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                        <span className="text-sm text-green-800 dark:text-green-200 font-medium">
                          Total weight: {Number(totalWeight(template.criteria)).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    {template.criteria.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        <p className="mb-2">No criteria added yet.</p>
                        <p className="text-sm">Click "Add Criteria" to create evaluation categories like Compliance, Empathy, Resolution, etc.</p>
                        <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
                          If you ran the test setup script, criteria should appear here. Try refreshing if they don't show up.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {template.criteria.map((criteria) => {
                          const isEditingCriteria = editingCriteria === criteria.id

                          return (
                            <div
                              key={criteria.id}
                              className="border-2 border-gray-200 dark:border-gray-700 rounded-xl p-5 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all hover:border-brand-300 dark:hover:border-brand-700"
                            >
                              {isEditingCriteria ? (
                                <CriteriaEditor
                                  criteria={criteria}
                                  onSave={(updates) => {
                                    handleUpdateCriteria(template.id, criteria.id, updates)
                                  }}
                                  onCancel={() => setEditingCriteria(null)}
                                />
                              ) : (
                                <div>
                                  <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                      <div className="flex items-center flex-wrap gap-2 mb-3">
                                        <h4 className="font-bold text-gray-900 dark:text-white text-lg flex items-center space-x-2">
                                          <FaBullseye className="w-5 h-5 text-brand-500" />
                                          <span>{criteria.category_name}</span>
                                        </h4>
                                        <span className="text-xs px-3 py-1.5 bg-gradient-to-r from-purple-100 to-purple-50 dark:from-purple-900/30 dark:to-purple-800/20 text-purple-700 dark:text-purple-300 rounded-full font-medium shadow-sm">
                                          Weight: {criteria.weight}%
                                        </span>
                                        <span className="text-xs px-3 py-1.5 bg-gradient-to-r from-blue-100 to-blue-50 dark:from-blue-900/30 dark:to-blue-800/20 text-blue-700 dark:text-blue-300 rounded-full font-medium shadow-sm">
                                          Passing: {criteria.passing_score}%
                                        </span>
                                        {criteria.rubric_levels && criteria.rubric_levels.length > 0 && (
                                          <span className="text-xs px-3 py-1.5 bg-gradient-to-r from-green-100 to-green-50 dark:from-green-900/30 dark:to-green-800/20 text-green-700 dark:text-green-300 rounded-full font-medium shadow-sm">
                                            {criteria.rubric_levels.length} Rubric {criteria.rubric_levels.length === 1 ? 'Level' : 'Levels'}
                                          </span>
                                        )}
                                      </div>
                                      <div className="mt-3 mb-4">
                                        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase tracking-wide">Evaluation Prompt:</p>
                                        <div className="bg-gradient-to-r from-gray-50 to-gray-100/50 dark:from-gray-900/50 dark:to-gray-800/30 p-3 rounded-lg border-l-4 border-brand-400 dark:border-brand-600">
                                          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                            {criteria.evaluation_prompt}
                                          </p>
                                        </div>
                                      </div>
                                      
                                      {/* Rubric Levels Section */}
                                      <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
                                        <div className="flex items-center justify-between mb-3">
                                          <div className="flex items-center space-x-2">
                                            <FaRuler className="w-4 h-4 text-brand-500" />
                                            <span className="text-sm font-bold text-gray-700 dark:text-gray-300">Rubric Levels</span>
                                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                              ({criteria.rubric_levels?.length || 0} {criteria.rubric_levels?.length === 1 ? 'level' : 'levels'})
                                            </span>
                                          </div>
                                          <button
                                            onClick={() => toggleCriteriaExpanded(criteria.id)}
                                            className="px-3 py-1.5 text-xs font-medium bg-brand-100 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 rounded-lg hover:bg-brand-200 dark:hover:bg-brand-900/50 transition-colors flex items-center space-x-1"
                                          >
                                            {expandedCriteria.has(criteria.id) ? (
                                              <>
                                                <FaChevronDown className="w-3 h-3" />
                                                <span>Hide Levels</span>
                                              </>
                                            ) : (
                                              <>
                                                <FaChevronRight className="w-3 h-3" />
                                                <span>Show Levels</span>
                                              </>
                                            )}
                                          </button>
                                        </div>
                                        
                                        {expandedCriteria.has(criteria.id) && (
                                          <div className="mt-2 space-y-2">
                                            {criteria.rubric_levels && criteria.rubric_levels.length > 0 ? (
                                              <div className="space-y-2">
                                                {[...criteria.rubric_levels].sort((a, b) => a.level_order - b.level_order).map((level) => {
                                                  const isEditing = editingRubricLevel === level.id
                                                  return (
                                                    <div
                                                      key={level.id}
                                                      className="p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-900/40 dark:to-gray-800/20 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-brand-300 dark:hover:border-brand-700 transition-all shadow-sm"
                                                    >
                                                      {isEditing ? (
                                                        <RubricLevelEditor
                                                          level={level}
                                                          onSave={(updates) => handleUpdateRubricLevel(template.id, criteria.id, level.id, updates)}
                                                          onCancel={() => setEditingRubricLevel(null)}
                                                        />
                                                      ) : (
                                                        <div className="flex items-start justify-between">
                                                          <div className="flex-1">
                                                            <div className="flex items-center flex-wrap gap-2 mb-2">
                                                              <span className="font-bold text-base text-gray-900 dark:text-white">
                                                                {level.level_name}
                                                              </span>
                                                              <span className="text-xs px-2.5 py-1 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-full font-semibold shadow-sm">
                                                                {level.min_score}-{level.max_score}
                                                              </span>
                                                              <span className="text-xs px-2.5 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full font-medium">
                                                                #{level.level_order}
                                                              </span>
                                                            </div>
                                                            <div className="mb-2">
                                                              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                                                {level.description}
                                                              </p>
                                                            </div>
                                                            {level.examples && (
                                                              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                                                                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1 flex items-center space-x-1">
                                                                  <FaLightbulb className="w-3 h-3" />
                                                                  <span>Examples:</span>
                                                                </p>
                                                                <p className="text-xs text-gray-600 dark:text-gray-400 italic leading-relaxed">
                                                                  {level.examples}
                                                                </p>
                                                              </div>
                                                            )}
                                                          </div>
                                                          <div className="flex items-center space-x-1 ml-2">
                                                            <button
                                                              onClick={() => setEditingRubricLevel(level.id)}
                                                              disabled={saving}
                                                              className="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded disabled:opacity-50"
                                                              title="Edit rubric level"
                                                            >
                                                              <FaEdit className="w-3 h-3" />
                                                            </button>
                                                            <button
                                                              onClick={() => handleDeleteRubricLevel(template.id, criteria.id, level.id)}
                                                              disabled={saving}
                                                              className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50"
                                                              title="Delete rubric level"
                                                            >
                                                              <FaTrash className="w-3 h-3" />
                                                            </button>
                                                          </div>
                                                        </div>
                                                      )}
                                                    </div>
                                                  )
                                                })}
                                                <button
                                                  onClick={() => {
                                                    // Add new rubric level with default values
                                                    const existingLevels = criteria.rubric_levels || []
                                                    const maxOrder = existingLevels.length > 0 
                                                      ? Math.max(...existingLevels.map(l => l.level_order))
                                                      : 0
                                                    const maxMaxScore = existingLevels.length > 0
                                                      ? Math.max(...existingLevels.map(l => l.max_score))
                                                      : 100
                                                    
                                                    handleAddRubricLevel(template.id, criteria.id, {
                                                      level_name: 'New Level',
                                                      level_order: maxOrder + 1,
                                                      min_score: Math.max(0, maxMaxScore - 20),
                                                      max_score: maxMaxScore,
                                                      description: 'Describe what constitutes this level of performance...',
                                                      examples: null
                                                    })
                                                  }}
                                                  disabled={saving}
                                                  className="w-full px-4 py-2.5 text-sm font-medium bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:from-purple-600 hover:to-purple-700 flex items-center justify-center space-x-2 disabled:opacity-50 shadow-md hover:shadow-lg transition-all"
                                                >
                                                  <FaPlus className="w-4 h-4" />
                                                  <span>Add Rubric Level</span>
                                                </button>
                                              </div>
                                            ) : (
                                              <div className="text-center py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50/50 dark:bg-gray-900/20">
                                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 font-medium">
                                                  No rubric levels defined yet
                                                </p>
                                                <p className="text-xs text-gray-500 dark:text-gray-500 mb-4">
                                                  Add performance levels to define scoring criteria (e.g., Excellent, Good, Average, Poor, Unacceptable)
                                                </p>
                                                <button
                                                  onClick={() => {
                                                    handleAddRubricLevel(template.id, criteria.id, {
                                                      level_name: 'Excellent',
                                                      level_order: 1,
                                                      min_score: 90,
                                                      max_score: 100,
                                                      description: 'Exceeds all expectations. Perfect execution.',
                                                      examples: null
                                                    })
                                                  }}
                                                  disabled={saving}
                                                  className="px-4 py-2 text-sm font-medium bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 shadow-md hover:shadow-lg transition-all"
                                                >
                                                  <FaPlus className="w-4 h-4 inline mr-2" />
                                                  Add First Level
                                                </button>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2 ml-4">
                                      <button
                                        onClick={() => setEditingCriteria(criteria.id)}
                                        disabled={saving}
                                        className="p-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded disabled:opacity-50"
                                        title="Edit this criteria"
                                      >
                                        <FaEdit className="w-4 h-4" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteCriteria(template.id, criteria.id)}
                                        disabled={saving}
                                        className="p-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50"
                                        title="Delete this criteria"
                                      >
                                        <FaTrash className="w-4 h-4" />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function RubricLevelEditor({
  level,
  onSave,
  onCancel,
}: {
  level: RubricLevel
  onSave: (updates: Partial<RubricLevel>) => void
  onCancel: () => void
}) {
  const [levelName, setLevelName] = useState(level.level_name)
  const [levelOrder, setLevelOrder] = useState(level.level_order.toString())
  const [minScore, setMinScore] = useState(level.min_score.toString())
  const [maxScore, setMaxScore] = useState(level.max_score.toString())
  const [description, setDescription] = useState(level.description)
  const [examples, setExamples] = useState(level.examples || '')

  const handleSave = () => {
    onSave({
      level_name: levelName,
      level_order: parseInt(levelOrder) || 1,
      min_score: parseInt(minScore) || 0,
      max_score: parseInt(maxScore) || 100,
      description: description,
      examples: examples || null
    })
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Level Name
          </label>
          <input
            type="text"
            value={levelName}
            onChange={(e) => setLevelName(e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            placeholder="e.g., Excellent, Good, Average"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Order (1 = highest)
          </label>
          <input
            type="number"
            value={levelOrder}
            onChange={(e) => setLevelOrder(e.target.value)}
            min="1"
            max="10"
            className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Min Score
          </label>
          <input
            type="number"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            min="0"
            max="100"
            className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Score
          </label>
          <input
            type="number"
            value={maxScore}
            onChange={(e) => setMaxScore(e.target.value)}
            min="0"
            max="100"
            className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Description (What constitutes this level?)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          placeholder="Describe what performance looks like at this level..."
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Examples (Optional)
        </label>
        <textarea
          value={examples}
          onChange={(e) => setExamples(e.target.value)}
          rows={2}
          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          placeholder="Examples of behaviors or actions that match this level..."
        />
      </div>
      <div className="flex items-center space-x-2">
        <button
          onClick={handleSave}
          className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center space-x-1"
        >
          <FaCheck className="w-3 h-3" />
          <span>Save</span>
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-1"
        >
          <FaTimes className="w-3 h-3" />
          <span>Cancel</span>
        </button>
      </div>
    </div>
  )
}

function CriteriaEditor({
  criteria,
  onSave,
  onCancel,
}: {
  criteria: EvaluationCriteria
  onSave: (updates: Partial<EvaluationCriteria>) => void
  onCancel: () => void
}) {
  const [categoryName, setCategoryName] = useState(criteria.category_name)
  const [weight, setWeight] = useState(criteria.weight.toString())
  const [passingScore, setPassingScore] = useState(criteria.passing_score.toString())
  const [evaluationPrompt, setEvaluationPrompt] = useState(criteria.evaluation_prompt)

  const handleSave = () => {
    onSave({
      category_name: categoryName,
      weight: parseFloat(weight) || 0,
      passing_score: parseInt(passingScore) || 0,
      evaluation_prompt: evaluationPrompt,
    } as Partial<EvaluationCriteria>)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Category Name
        </label>
        <input
          type="text"
          value={categoryName}
          onChange={(e) => setCategoryName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          placeholder="e.g., Compliance, Empathy, Resolution"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Weight (%)
          </label>
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            min="0"
            max="100"
            step="0.1"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Passing Score (0-100)
          </label>
          <input
            type="number"
            value={passingScore}
            onChange={(e) => setPassingScore(e.target.value)}
            min="0"
            max="100"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          LLM Evaluation Prompt
        </label>
        <textarea
          value={evaluationPrompt}
          onChange={(e) => setEvaluationPrompt(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          placeholder="Instructions for the LLM on how to evaluate this category..."
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          This prompt will be sent to the LLM to evaluate this category. Be specific about what to look for.
        </p>
      </div>
      <div className="flex space-x-2">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 flex items-center space-x-1"
        >
          <FaCheck className="w-4 h-4" />
          <span>Save</span>
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-1"
        >
          <FaTimes className="w-4 h-4" />
          <span>Cancel</span>
        </button>
      </div>
    </div>
  )
}