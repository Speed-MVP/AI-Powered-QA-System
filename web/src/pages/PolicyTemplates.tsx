import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle, FaSpinner, FaLightbulb, FaCheckCircle, FaChevronDown, FaChevronRight, FaMagic, FaList, FaShieldAlt } from 'react-icons/fa'

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
  policy_rules?: any
  policy_rules_version?: number
  enable_structured_rules?: boolean
}

export function PolicyTemplates() {
  const [templates, setTemplates] = useState<PolicyTemplate[]>([])
  const [activeTemplate, setActiveTemplate] = useState<PolicyTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<string | null>(null)
  const [editingTemplateName, setEditingTemplateName] = useState('')
  const [editingTemplateDesc, setEditingTemplateDesc] = useState('')
  const [editingCriteria, setEditingCriteria] = useState<string | null>(null)
  const [editingRubricLevel, setEditingRubricLevel] = useState<string | null>(null)
  const [expandedCriteria, setExpandedCriteria] = useState<Set<string>>(new Set())
  const [newTemplateName, setNewTemplateName] = useState('')
  const [newTemplateDesc, setNewTemplateDesc] = useState('')
  const [showNewTemplate, setShowNewTemplate] = useState(false)
  const [showTemplateDropdown, setShowTemplateDropdown] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingRulesForCategory, setEditingRulesForCategory] = useState<{templateId: string, categoryName: string} | null>(null)

  // Fetch templates from backend
  useEffect(() => {
    loadTemplates()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showTemplateDropdown && !(event.target as Element).closest('.template-dropdown-container')) {
        setShowTemplateDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showTemplateDropdown])

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

  const handleCreatePrebuiltTemplate = async () => {
    try {
      setSaving(true)
      setError(null)
      setShowTemplateDropdown(false)
      
      const newTemplate = await api.createPrebuiltTemplate()
      
      setTemplates(prev => [...prev, newTemplate])
      await loadTemplates() // Reload to get full template data with criteria
    } catch (err: any) {
      setError(err.message || 'Failed to create pre-built template')
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
      setEditingTemplateName('')
      setEditingTemplateDesc('')
    } catch (err: any) {
      setError(err.message || 'Failed to update template')
    } finally {
      setSaving(false)
    }
  }

  const handleStartEditTemplate = (template: PolicyTemplate) => {
    setEditingTemplate(template.id)
    setEditingTemplateName(template.template_name)
    setEditingTemplateDesc(template.description || '')
  }

  const handleSaveTemplateEdit = (templateId: string) => {
    handleUpdateTemplate(templateId, {
      template_name: editingTemplateName,
      description: editingTemplateDesc || undefined
    })
  }

  const handleCancelTemplateEdit = () => {
    setEditingTemplate(null)
    setEditingTemplateName('')
    setEditingTemplateDesc('')
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

  const handleGenerateRules = async (templateId: string) => {
    if (!confirm('Generate policy rules for this template? This will overwrite any existing rules.')) return

    try {
      setSaving(true)
      setError(null)
      
      const result = await api.generateRulesForTemplate(templateId)
      
      alert(`Rules generated successfully! Version: ${result.rules_version}, Categories: ${result.categories.join(', ')}`)
      
      // Reload templates to get updated state
      await loadTemplates()
    } catch (err: any) {
      setError(err.message || 'Failed to generate rules')
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">
                Policy Templates
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage evaluation criteria and rubric levels for quality assurance
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadTemplates}
                disabled={loading}
                className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors disabled:opacity-50"
                title="Refresh templates"
              >
                <FaSpinner className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
              <div className="relative template-dropdown-container">
                <button
                  onClick={() => setShowTemplateDropdown(!showTemplateDropdown)}
                  disabled={saving || showNewTemplate}
                  className="px-4 py-2 text-sm bg-brand-500 text-white rounded-md hover:bg-brand-600 flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  <FaPlus className="w-4 h-4" />
                  <span>New Template</span>
                  <FaChevronDown className={`w-3 h-3 transition-transform ${showTemplateDropdown ? 'rotate-180' : ''}`} />
                </button>
                
                {showTemplateDropdown && (
                  <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg z-10">
                    <div className="p-2">
                      <button
                        onClick={handleCreatePrebuiltTemplate}
                        disabled={saving}
                        className="w-full text-left px-4 py-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                      >
                        <div className="font-medium text-gray-900 dark:text-white mb-1">
                          Pre-built Standard QA Template
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Includes 5 pre-configured criteria: Compliance, Communication Skills, Empathy, Problem-Solving, and Resolution. Ready to use immediately.
                        </div>
                      </button>
                      <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>
                      <button
                        onClick={() => {
                          setShowTemplateDropdown(false)
                          setShowNewTemplate(true)
                        }}
                        disabled={saving}
                        className="w-full text-left px-4 py-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                      >
                        <div className="font-medium text-gray-900 dark:text-white mb-1">
                          Empty Template
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Start from scratch. Create your own criteria and rubric levels.
                        </div>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-center gap-3">
            <FaExclamationCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
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
          <div className="mb-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Create New Template
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Template Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTemplateName}
                  onChange={(e) => setNewTemplateName(e.target.value)}
                  placeholder="e.g., Customer Service QA, Sales Call Evaluation"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Description
                </label>
                <textarea
                  value={newTemplateDesc}
                  onChange={(e) => setNewTemplateDesc(e.target.value)}
                  placeholder="Describe what this template evaluates"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleCreateTemplate}
                  disabled={saving || !newTemplateName.trim()}
                  className="px-4 py-2 text-sm bg-brand-500 text-white rounded-md hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium"
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
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Templates Grid */}
        {templates.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No templates yet. Create your first template to get started.
            </p>
            <button
              onClick={() => setShowNewTemplate(true)}
              className="px-4 py-2 text-sm bg-brand-500 text-white rounded-md hover:bg-brand-600 transition-colors"
            >
              Create Template
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {templates.map((template) => {
              const isActive = activeTemplate?.id === template.id
              const weightsValid = validateWeight(template.criteria)
              const isEditing = editingTemplate === template.id

              return (
                <div
                  key={template.id}
                  className={`bg-white dark:bg-gray-800 border rounded-md transition-all ${
                    isActive
                      ? 'border-brand-500 dark:border-brand-500'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  {/* Template Header */}
                  <div className="p-5 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex-1 min-w-0">
                        {isEditing ? (
                          <div className="space-y-3">
                            <input
                              type="text"
                              value={editingTemplateName}
                              onChange={(e) => setEditingTemplateName(e.target.value)}
                              className="text-lg font-semibold px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full focus:outline-none focus:ring-2 focus:ring-brand-500"
                            />
                            <textarea
                              value={editingTemplateDesc}
                              onChange={(e) => setEditingTemplateDesc(e.target.value)}
                              rows={2}
                              className="text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                            />
                          </div>
                        ) : (
                          <div>
                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                {template.template_name}
                              </h2>
                              {isActive && (
                                <span className="px-2 py-0.5 bg-brand-500 text-white text-xs font-medium rounded flex items-center gap-1">
                                  <FaCheckCircle className="w-3 h-3" />
                                  <span>Active</span>
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {template.description || 'No description'}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {!isEditing && (
                          <>
                            <button
                              onClick={() => handleGenerateRules(template.id)}
                              disabled={saving}
                              className="px-2.5 py-1.5 text-xs bg-purple-500 text-white rounded-md hover:bg-purple-600 disabled:opacity-50 transition-colors flex items-center gap-1"
                              title="Generate Policy Rules (Temporary)"
                            >
                              <FaMagic className="w-3 h-3" />
                              <span className="hidden sm:inline">Generate Rules</span>
                            </button>
                            <button
                              onClick={() => handleSetActive(template.id)}
                              disabled={saving}
                              className={`px-2.5 py-1.5 text-xs rounded-md disabled:opacity-50 transition-colors ${
                                isActive
                                  ? 'bg-brand-500 text-white'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              {isActive ? 'Active' : 'Set Active'}
                            </button>
                            <button
                              onClick={() => handleStartEditTemplate(template)}
                              disabled={saving}
                              className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded disabled:opacity-50 transition-colors"
                              title="Edit template"
                            >
                              <FaEdit className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        {isEditing && (
                          <>
                            <button
                              onClick={() => handleSaveTemplateEdit(template.id)}
                              disabled={saving || !editingTemplateName.trim()}
                              className="p-1.5 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded disabled:opacity-50 transition-colors"
                              title="Save changes"
                            >
                              <FaSave className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={handleCancelTemplateEdit}
                              disabled={saving}
                              className="p-1.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded disabled:opacity-50 transition-colors"
                              title="Cancel editing"
                            >
                              <FaTimes className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDeleteTemplate(template.id)}
                          disabled={saving}
                          className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50 transition-colors"
                          title="Delete template"
                        >
                          <FaTrash className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Criteria Section */}
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                          Evaluation Criteria
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {template.criteria.length} {template.criteria.length === 1 ? 'category' : 'categories'}
                        </p>
                      </div>
                      <button
                        onClick={() => {
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
                        className="px-3 py-1.5 text-xs bg-brand-500 text-white rounded-md hover:bg-brand-600 flex items-center gap-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                        title={totalWeight(template.criteria) >= 100 ? "Total weight already equals 100%" : "Add a new evaluation criteria"}
                      >
                        <FaPlus className="w-3 h-3" />
                        <span>Add Criteria</span>
                      </button>
                    </div>

                    {/* Weight Validation */}
                    {!weightsValid && template.criteria.length > 0 && (
                      <div className="mb-3 p-2.5 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md flex items-start gap-2">
                        <FaExclamationCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-xs font-medium text-yellow-800 dark:text-yellow-200">
                            Weight Total Invalid
                          </p>
                          <p className="text-xs text-yellow-700 dark:text-yellow-300">
                            Total must equal 100%. Current: <span className="font-semibold">{Number(totalWeight(template.criteria)).toFixed(1)}%</span>
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Weight Summary */}
                    {weightsValid && template.criteria.length > 0 && (
                      <div className="mb-3 p-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md flex items-center gap-2">
                        <FaCheckCircle className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                        <span className="text-xs text-green-800 dark:text-green-200 font-medium">
                          Total weight: {Number(totalWeight(template.criteria)).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    {template.criteria.length === 0 ? (
                      <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                        <p className="text-sm mb-1">No criteria added yet.</p>
                        <p className="text-xs">Click "Add Criteria" to create evaluation categories.</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {template.criteria.map((criteria) => {
                          const isEditingCriteria = editingCriteria === criteria.id

                          return (
                            <div
                              key={criteria.id}
                              className="border border-gray-200 dark:border-gray-700 rounded-md p-4 bg-gray-50 dark:bg-gray-900/50 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
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
                                  <div className="flex items-start justify-between gap-3 mb-3">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                                        <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
                                          {criteria.category_name}
                                        </h4>
                                        <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded font-medium">
                                          {criteria.weight}%
                                        </span>
                                        <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded font-medium">
                                          Pass: {criteria.passing_score}%
                                        </span>
                                        {criteria.rubric_levels && criteria.rubric_levels.length > 0 && (
                                          <span className="text-xs px-2 py-0.5 bg-brand-100 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 rounded font-medium">
                                            {criteria.rubric_levels.length} {criteria.rubric_levels.length === 1 ? 'Level' : 'Levels'}
                                          </span>
                                        )}
                                        {template.policy_rules?.rules?.[criteria.category_name] && (
                                          <>
                                            <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded font-medium flex items-center gap-1">
                                              <FaShieldAlt className="w-2.5 h-2.5" />
                                              {template.policy_rules.rules[criteria.category_name].length} {template.policy_rules.rules[criteria.category_name].length === 1 ? 'Rule' : 'Rules'}
                                            </span>
                                            {template.policy_rules.rules[criteria.category_name].some((r: any) => r.critical) && (
                                              <span className="text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded font-medium">
                                                Critical
                                              </span>
                                            )}
                                          </>
                                        )}
                                      </div>
                                      <div className="mb-3">
                                        <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Evaluation Prompt:</p>
                                        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-2.5">
                                          <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                                            {criteria.evaluation_prompt}
                                          </p>
                                        </div>
                                      </div>
                                      
                                      {/* Rubric Levels Section */}
                                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                        <div className="flex items-center justify-between mb-2">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Rubric Levels</span>
                                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                              ({criteria.rubric_levels?.length || 0})
                                            </span>
                                          </div>
                                          <button
                                            onClick={() => toggleCriteriaExpanded(criteria.id)}
                                            className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center gap-1"
                                          >
                                            {expandedCriteria.has(criteria.id) ? (
                                              <>
                                                <FaChevronDown className="w-3 h-3" />
                                                <span>Hide</span>
                                              </>
                                            ) : (
                                              <>
                                                <FaChevronRight className="w-3 h-3" />
                                                <span>Show</span>
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
                                                      className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
                                                    >
                                                      {isEditing ? (
                                                        <RubricLevelEditor
                                                          level={level}
                                                          onSave={(updates) => handleUpdateRubricLevel(template.id, criteria.id, level.id, updates)}
                                                          onCancel={() => setEditingRubricLevel(null)}
                                                        />
                                                      ) : (
                                                        <div className="flex items-start justify-between gap-2">
                                                          <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                                              <span className="font-medium text-sm text-gray-900 dark:text-white">
                                                                {level.level_name}
                                                              </span>
                                                              <span className="text-xs px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded font-medium">
                                                                {level.min_score}-{level.max_score}
                                                              </span>
                                                              <span className="text-xs px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded font-medium">
                                                                #{level.level_order}
                                                              </span>
                                                            </div>
                                                            <div className="mb-1.5">
                                                              <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                                                                {level.description}
                                                              </p>
                                                            </div>
                                                            {level.examples && (
                                                              <div className="mt-1.5 pt-1.5 border-t border-gray-200 dark:border-gray-700">
                                                                <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5 flex items-center gap-1">
                                                                  <FaLightbulb className="w-3 h-3" />
                                                                  <span>Examples:</span>
                                                                </p>
                                                                <p className="text-xs text-gray-600 dark:text-gray-400 italic leading-relaxed">
                                                                  {level.examples}
                                                                </p>
                                                              </div>
                                                            )}
                                                          </div>
                                                          <div className="flex items-center gap-0.5 flex-shrink-0">
                                                            <button
                                                              onClick={() => setEditingRubricLevel(level.id)}
                                                              disabled={saving}
                                                              className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded disabled:opacity-50 transition-colors"
                                                              title="Edit rubric level"
                                                            >
                                                              <FaEdit className="w-3 h-3" />
                                                            </button>
                                                            <button
                                                              onClick={() => handleDeleteRubricLevel(template.id, criteria.id, level.id)}
                                                              disabled={saving}
                                                              className="p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50 transition-colors"
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
                                                    const existingLevels = criteria.rubric_levels || []
                                                    const maxOrder = existingLevels.length > 0 
                                                      ? Math.max(...existingLevels.map(l => l.level_order))
                                                      : 0
                                                    
                                                    const sortedLevels = [...existingLevels].sort((a, b) => a.min_score - b.min_score)
                                                    
                                                    let newMinScore = 0
                                                    let newMaxScore = 20
                                                    
                                                    const overlapsWithExisting = (min: number, max: number) => {
                                                      return existingLevels.some(level => 
                                                        !(max < level.min_score || min > level.max_score)
                                                      )
                                                    }
                                                    
                                                    if (sortedLevels.length === 0) {
                                                      newMinScore = 0
                                                      newMaxScore = 20
                                                    } else {
                                                      const lowestMin = sortedLevels[0].min_score
                                                      if (lowestMin >= 20) {
                                                        newMinScore = Math.max(0, lowestMin - 20)
                                                        newMaxScore = lowestMin - 1
                                                      } else {
                                                        let foundGap = false
                                                        for (let i = 0; i < sortedLevels.length - 1; i++) {
                                                          const currentMax = sortedLevels[i].max_score
                                                          const nextMin = sortedLevels[i + 1].min_score
                                                          const gapSize = nextMin - currentMax - 1
                                                          
                                                          if (gapSize >= 10) {
                                                            newMinScore = currentMax + 1
                                                            newMaxScore = Math.min(100, currentMax + Math.min(20, gapSize))
                                                            foundGap = true
                                                            break
                                                          }
                                                        }
                                                        
                                                        if (!foundGap) {
                                                          const highestMax = Math.max(...sortedLevels.map(l => l.max_score))
                                                          if (highestMax < 80) {
                                                            newMinScore = highestMax + 1
                                                            newMaxScore = Math.min(100, highestMax + 20)
                                                          } else {
                                                            if (lowestMin > 0) {
                                                              newMinScore = Math.max(0, lowestMin - 10)
                                                              newMaxScore = Math.max(0, lowestMin - 1)
                                                            } else {
                                                              newMinScore = 0
                                                              newMaxScore = 10
                                                            }
                                                          }
                                                        }
                                                      }
                                                      
                                                      if (overlapsWithExisting(newMinScore, newMaxScore)) {
                                                        for (let testMin = 0; testMin <= 90; testMin += 10) {
                                                          const testMax = Math.min(100, testMin + 10)
                                                          if (!overlapsWithExisting(testMin, testMax)) {
                                                            newMinScore = testMin
                                                            newMaxScore = testMax
                                                            break
                                                          }
                                                        }
                                                      }
                                                    }
                                                    
                                                    handleAddRubricLevel(template.id, criteria.id, {
                                                      level_name: 'New Level',
                                                      level_order: maxOrder + 1,
                                                      min_score: newMinScore,
                                                      max_score: newMaxScore,
                                                      description: 'Describe what constitutes this level of performance...',
                                                      examples: null
                                                    })
                                                  }}
                                                  disabled={saving}
                                                  className="w-full px-3 py-2 text-xs font-medium bg-brand-500 text-white rounded-md hover:bg-brand-600 flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
                                                >
                                                  <FaPlus className="w-3 h-3" />
                                                  <span>Add Rubric Level</span>
                                                </button>
                                              </div>
                                            ) : (
                                              <div className="text-center py-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-900/30">
                                                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 font-medium">
                                                  No rubric levels defined yet
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
                                                  className="px-3 py-1.5 text-xs font-medium bg-brand-500 text-white rounded-md hover:bg-brand-600 disabled:opacity-50 transition-colors"
                                                >
                                                  <FaPlus className="w-3 h-3 inline mr-1" />
                                                  Add First Level
                                                </button>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-1 flex-shrink-0">
                                      {template.policy_rules?.rules?.[criteria.category_name] && (
                                        <button
                                          onClick={() => setEditingRulesForCategory({templateId: template.id, categoryName: criteria.category_name})}
                                          disabled={saving}
                                          className="p-1.5 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded disabled:opacity-50 transition-colors"
                                          title="Edit policy rules for this category"
                                        >
                                          <FaList className="w-3.5 h-3.5" />
                                        </button>
                                      )}
                                      <button
                                        onClick={() => setEditingCriteria(criteria.id)}
                                        disabled={saving}
                                        className="p-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded disabled:opacity-50 transition-colors"
                                        title="Edit this criteria"
                                      >
                                        <FaEdit className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteCriteria(template.id, criteria.id)}
                                        disabled={saving}
                                        className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50 transition-colors"
                                        title="Delete this criteria"
                                      >
                                        <FaTrash className="w-3.5 h-3.5" />
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

        {/* Rule Editor Modal */}
        {editingRulesForCategory && (() => {
          const template = templates.find(t => t.id === editingRulesForCategory.templateId)
          const rules = template?.policy_rules?.rules?.[editingRulesForCategory.categoryName] || []
          
          return (
            <RuleEditorModal
              templateId={editingRulesForCategory.templateId}
              categoryName={editingRulesForCategory.categoryName}
              rules={rules}
              onClose={() => setEditingRulesForCategory(null)}
              onSave={async (updatedRules) => {
                try {
                  setSaving(true)
                  setError(null)
                  
                  const template = templates.find(t => t.id === editingRulesForCategory.templateId)
                  if (!template || !template.policy_rules) return
                  
                  const updatedPolicyRules = {
                    ...template.policy_rules,
                    rules: {
                      ...template.policy_rules.rules,
                      [editingRulesForCategory.categoryName]: updatedRules
                    }
                  }
                  
                  const updated = await api.updatePolicyRules(editingRulesForCategory.templateId, updatedPolicyRules)
                  
                  setTemplates(prev => prev.map(t => t.id === editingRulesForCategory.templateId ? updated : t))
                  if (activeTemplate?.id === editingRulesForCategory.templateId) {
                    setActiveTemplate(updated)
                  }
                  
                  setEditingRulesForCategory(null)
                } catch (err: any) {
                  setError(err.message || 'Failed to update rules')
                } finally {
                  setSaving(false)
                }
              }}
            />
          )
        })()}
      </div>
    </div>
  )
}

function RuleEditorModal({
  templateId,
  categoryName,
  rules,
  onClose,
  onSave
}: {
  templateId: string
  categoryName: string
  rules: any[]
  onClose: () => void
  onSave: (updatedRules: any[]) => void
}) {
  const [editedRules, setEditedRules] = useState<any[]>(rules.map(r => ({ ...r })))
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(editedRules)
    } finally {
      setSaving(false)
    }
  }

  const updateRule = (index: number, field: string, value: any) => {
    setEditedRules(prev => prev.map((r, i) => 
      i === index ? { ...r, [field]: value } : r
    ))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Edit Rules: {categoryName}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {rules.length} {rules.length === 1 ? 'rule' : 'rules'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <FaTimes className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {editedRules.map((rule, index) => (
              <div
                key={rule.id || index}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-900/50"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      {rule.description || `Rule ${index + 1}`}
                    </h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Type: <span className="font-mono">{rule.type}</span> | ID: <span className="font-mono">{rule.id}</span>
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`critical-${index}`}
                      checked={rule.critical || false}
                      onChange={(e) => updateRule(index, 'critical', e.target.checked)}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 dark:focus:ring-red-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                    <label
                      htmlFor={`critical-${index}`}
                      className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1"
                    >
                      <FaExclamationCircle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                      Critical Rule
                    </label>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`enabled-${index}`}
                      checked={rule.enabled !== false}
                      onChange={(e) => updateRule(index, 'enabled', e.target.checked)}
                      className="w-4 h-4 text-brand-600 bg-gray-100 border-gray-300 rounded focus:ring-brand-500 dark:focus:ring-brand-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                    <label
                      htmlFor={`enabled-${index}`}
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Enabled
                    </label>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Severity
                    </label>
                    <select
                      value={rule.severity || 'minor'}
                      onChange={(e) => updateRule(index, 'severity', e.target.value)}
                      className="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="minor">Minor</option>
                      <option value="moderate">Moderate</option>
                      <option value="major">Major</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
            
            {editedRules.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>No rules found for this category</p>
              </div>
            )}
          </div>
        </div>
        
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-brand-500 text-white rounded-md hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium"
          >
            {saving ? (
              <>
                <FaSpinner className="w-4 h-4 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <FaSave className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
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
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Level Name
          </label>
          <input
            type="text"
            value={levelName}
            onChange={(e) => setLevelName(e.target.value)}
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="e.g., Excellent, Good"
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
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
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
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
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
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
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
          className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          placeholder="Examples of behaviors or actions..."
        />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <button
          onClick={handleSave}
          className="px-3 py-1.5 text-xs bg-brand-500 text-white rounded-md hover:bg-brand-600 flex items-center gap-1.5 transition-colors font-medium"
        >
          <FaCheck className="w-3 h-3" />
          <span>Save</span>
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center gap-1.5 transition-colors"
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
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          Category Name
        </label>
        <input
          type="text"
          value={categoryName}
          onChange={(e) => setCategoryName(e.target.value)}
          className="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="e.g., Compliance, Empathy, Resolution"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Weight (%)
          </label>
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            min="0"
            max="100"
            step="0.1"
            className="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Passing Score (0-100)
          </label>
          <input
            type="number"
            value={passingScore}
            onChange={(e) => setPassingScore(e.target.value)}
            min="0"
            max="100"
            className="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          LLM Evaluation Prompt
        </label>
        <textarea
          value={evaluationPrompt}
          onChange={(e) => setEvaluationPrompt(e.target.value)}
          rows={3}
          className="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          placeholder="Instructions for the LLM on how to evaluate this category..."
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          This prompt will be sent to the LLM to evaluate this category.
        </p>
      </div>
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSave}
          className="px-3 py-1.5 text-xs bg-brand-500 text-white rounded-md hover:bg-brand-600 flex items-center gap-1.5 transition-colors font-medium"
        >
          <FaCheck className="w-3 h-3" />
          <span>Save</span>
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center gap-1.5 transition-colors"
        >
          <FaTimes className="w-3 h-3" />
          <span>Cancel</span>
        </button>
      </div>
    </div>
  )
}