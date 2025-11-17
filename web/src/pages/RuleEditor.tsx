/**
 * Rule Editor Main Screen
 * Phase 5: Structured Rule Editor UI & Admin Tools
 * 
 * Main screen for viewing and editing structured policy rules.
 * Features:
 * - Header with policy name, version, last published info
 * - Top bar actions (Save Draft, Preview, Publish, Discard, History)
 * - Left column: Category accordion
 * - Main pane: Rule list (sortable, filterable)
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaSave, FaEye, FaRocket, FaTrash, FaHistory, FaChevronDown, FaChevronRight, FaEdit, FaToggleOn, FaToggleOff } from 'react-icons/fa'

interface Rule {
  id: string
  type: string
  category: string
  severity: string
  enabled: boolean
  description: string
  critical?: boolean
}

interface PolicyRules {
  version: number
  rules: {
    [category: string]: Rule[]
  }
  metadata?: any
}

export function RuleEditor() {
  const { templateId } = useParams<{ templateId: string }>()
  const navigate = useNavigate()
  const [rules, setRules] = useState<PolicyRules | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
  const [templateInfo, setTemplateInfo] = useState<any>(null)

  useEffect(() => {
    if (templateId) {
      loadRules()
      loadTemplateInfo()
    }
  }, [templateId])

  const loadRules = async () => {
    if (!templateId) return
    
    try {
      setLoading(true)
      const data = await api.get(`/api/policy-templates/${templateId}/rules`)
      setRules(data.rules)
      if (data.rules?.rules) {
        const firstCategory = Object.keys(data.rules.rules)[0]
        if (firstCategory) {
          setSelectedCategory(firstCategory)
          setExpandedCategories(new Set([firstCategory]))
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load rules')
    } finally {
      setLoading(false)
    }
  }

  const loadTemplateInfo = async () => {
    if (!templateId) return
    
    try {
      const data = await api.get(`/api/templates/${templateId}`)
      setTemplateInfo(data)
    } catch (err) {
      console.error('Failed to load template info:', err)
    }
  }

  const handleSaveDraft = async () => {
    if (!templateId || !rules) return
    
    try {
      await api.post(`/api/policy-templates/${templateId}/rules/draft`, {
        rules: rules
      })
      alert('Draft saved successfully')
    } catch (err: any) {
      alert(`Failed to save draft: ${err.message}`)
    }
  }

  const handlePublish = async () => {
    if (!templateId) return
    
    if (!confirm('Are you sure you want to publish these rules? This will create a new version.')) {
      return
    }
    
    try {
      await api.post(`/api/policy-templates/${templateId}/rules/publish`, {
        reason: 'Published from rule editor'
      })
      alert('Rules published successfully')
      loadRules()
      loadTemplateInfo()
    } catch (err: any) {
      alert(`Failed to publish: ${err.message}`)
    }
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(category)) {
      newExpanded.delete(category)
    } else {
      newExpanded.add(category)
    }
    setExpandedCategories(newExpanded)
    setSelectedCategory(category)
  }

  if (loading) {
    return <div className="p-8">Loading rules...</div>
  }

  if (error) {
    return <div className="p-8 text-red-600">Error: {error}</div>
  }

  const categories = rules?.rules ? Object.keys(rules.rules) : []

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          {templateInfo?.template_name || 'Rule Editor'}
        </h1>
        <div className="text-sm text-gray-600">
          Current Version: {templateInfo?.rules_version || 'N/A'} | 
          Last Published: {templateInfo?.rules_generated_at ? new Date(templateInfo.rules_generated_at).toLocaleDateString() : 'Never'}
        </div>
      </div>

      {/* Top Bar Actions */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={handleSaveDraft}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
        >
          <FaSave /> Save Draft
        </button>
        <button
          onClick={() => navigate(`/rule-sandbox/${templateId}`)}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2"
        >
          <FaEye /> Preview
        </button>
        <button
          onClick={handlePublish}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-2"
        >
          <FaRocket /> Publish
        </button>
        <button
          onClick={() => navigate(`/rule-history/${templateId}`)}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center gap-2"
        >
          <FaHistory /> History
        </button>
      </div>

      <div className="flex gap-6">
        {/* Left Column: Category Accordion */}
        <div className="w-64 border-r pr-6">
          <h2 className="font-semibold mb-4">Categories</h2>
          {categories.map(category => (
            <div key={category} className="mb-2">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between p-2 hover:bg-gray-100 rounded"
              >
                <span>{category}</span>
                {expandedCategories.has(category) ? <FaChevronDown /> : <FaChevronRight />}
              </button>
              {expandedCategories.has(category) && (
                <div className="ml-4 text-sm text-gray-600">
                  {rules?.rules[category]?.length || 0} rules
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Main Pane: Rule List */}
        <div className="flex-1">
          {selectedCategory && rules?.rules[selectedCategory] ? (
            <div>
              <h2 className="text-xl font-semibold mb-4">{selectedCategory} Rules</h2>
              <div className="space-y-2">
                {rules.rules[selectedCategory].map(rule => (
                  <div
                    key={rule.id}
                    className="border p-4 rounded flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{rule.id}</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {rule.type}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded ${
                          rule.severity === 'critical' ? 'bg-red-100 text-red-800' :
                          rule.severity === 'major' ? 'bg-orange-100 text-orange-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {rule.severity}
                        </span>
                        {rule.critical && (
                          <span className="px-2 py-1 bg-red-200 text-red-900 text-xs rounded">
                            CRITICAL
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">{rule.description}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {/* Toggle enabled */}}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        {rule.enabled ? <FaToggleOn size={24} /> : <FaToggleOff size={24} />}
                      </button>
                      <button
                        onClick={() => {/* Edit rule */}}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <FaEdit />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <button
                onClick={() => {/* Add rule */}}
                className="mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Add Rule
              </button>
            </div>
          ) : (
            <div className="text-gray-500">Select a category to view rules</div>
          )}
        </div>
      </div>
    </div>
  )
}

