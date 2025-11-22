import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaPlus, FaSpinner, FaCheckCircle, FaExclamationCircle, FaEdit, FaTrash } from 'react-icons/fa'

interface FlowVersion {
  id: string
  company_id: string
  name: string
  description: string | null
  is_active: boolean
  version_number: number
  created_at: string
  updated_at: string
}

export function TemplatesPage() {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<FlowVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showNewTemplateModal, setShowNewTemplateModal] = useState(false)
  const [templateType, setTemplateType] = useState<'blank' | 'standard'>('blank')
  const [loadingStandard, setLoadingStandard] = useState(false)

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      setError(null)
      const versions = await api.listFlowVersions()
      setTemplates(versions)
    } catch (err: any) {
      setError(err.message || 'Failed to load templates')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadStandardTemplate = async () => {
    try {
      setLoadingStandard(true)
      setError(null)
      const response = await api.post('/api/templates/load-standard', {})
      
      // Show success message
      alert('Standard template loaded successfully!')
      
      // Close modal and reload templates
      setShowNewTemplateModal(false)
      setTemplateType('blank')
      await loadTemplates()
      
      // Optionally navigate to the SOP builder to view the new template
      navigate('/sop-builder')
    } catch (err: any) {
      setError(err.message || 'Failed to load standard template')
    } finally {
      setLoadingStandard(false)
    }
  }

  const handleCreateBlankTemplate = () => {
    // Navigate to SOP Builder to create a new template
    navigate('/sop-builder')
    setShowNewTemplateModal(false)
  }

  const handleDeleteTemplate = async (template: FlowVersion) => {
    if (!confirm(`Are you sure you want to delete "${template.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.deleteFlowVersion(template.id)
      await loadTemplates()
    } catch (err: any) {
      setError(err.message || 'Failed to delete template')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(120,119,198,0.1),transparent_50%)] pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 relative">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-brand-600">Templates</p>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Policy Templates</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Manage your QA templates (SOP, Compliance Rules, and Rubrics)
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setShowNewTemplateModal(true)}
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 flex items-center gap-2"
            >
              <FaPlus className="w-4 h-4" />
              New Template
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200 flex items-center gap-3">
            <FaExclamationCircle className="w-5 h-5 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-red-600 dark:text-red-400">
              ×
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <FaSpinner className="w-8 h-8 animate-spin text-brand-600" />
          </div>
        ) : (
          /* Templates List */
          <div className="rounded-2xl border border-gray-100 bg-white/80 shadow-sm dark:border-gray-800 dark:bg-gray-900/60 overflow-hidden">
            {templates.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-gray-500 dark:text-gray-400 mb-4">No templates yet</p>
                <button
                  onClick={() => setShowNewTemplateModal(true)}
                  className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
                >
                  Create Your First Template
                </button>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-100 dark:divide-gray-800">
                <thead className="bg-gray-50 dark:bg-gray-800/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      Template Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900/60 divide-y divide-gray-100 dark:divide-gray-800">
                  {templates.map((template) => (
                    <tr key={template.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {template.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Version {template.version_number}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 dark:text-gray-300">
                          {template.description || 'No description'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {template.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                            <FaCheckCircle className="w-3 h-3 mr-1" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(template.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => navigate('/sop-builder')}
                            className="text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
                            title="Edit Template"
                          >
                            <FaEdit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteTemplate(template)}
                            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                            title="Delete Template"
                          >
                            <FaTrash className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* New Template Modal */}
        {showNewTemplateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Create New Template
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Choose how you'd like to start
                </p>
              </div>
              
              <div className="p-6 space-y-4">
                {/* Template Type Selection */}
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Template Type
                  </label>
                  
                  <div className="space-y-2">
                    <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition hover:bg-gray-50 dark:hover:bg-gray-700/50"
                      style={{
                        borderColor: templateType === 'blank' ? 'rgb(99 102 241)' : 'rgb(229 231 235)',
                        backgroundColor: templateType === 'blank' ? 'rgba(99, 102, 241, 0.05)' : 'transparent'
                      }}
                    >
                      <input
                        type="radio"
                        name="templateType"
                        value="blank"
                        checked={templateType === 'blank'}
                        onChange={() => setTemplateType('blank')}
                        className="mt-1 mr-3"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">Blank Template</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          Start from scratch and build your own custom template
                        </div>
                      </div>
                    </label>
                    
                    <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition hover:bg-gray-50 dark:hover:bg-gray-700/50"
                      style={{
                        borderColor: templateType === 'standard' ? 'rgb(99 102 241)' : 'rgb(229 231 235)',
                        backgroundColor: templateType === 'standard' ? 'rgba(99, 102, 241, 0.05)' : 'transparent'
                      }}
                    >
                      <input
                        type="radio"
                        name="templateType"
                        value="standard"
                        checked={templateType === 'standard'}
                        onChange={() => setTemplateType('standard')}
                        className="mt-1 mr-3"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          Standard BPO Template (SOP-Driven)
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          Pre-built template with SOP, Compliance Rules, and Rubric for standard PH/US call center QA
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
                <button
                  onClick={() => {
                    setShowNewTemplateModal(false)
                    setTemplateType('blank')
                    setError(null)
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (templateType === 'standard') {
                      handleLoadStandardTemplate()
                    } else {
                      handleCreateBlankTemplate()
                    }
                  }}
                  disabled={loadingStandard}
                  className="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-md hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loadingStandard ? (
                    <>
                      <FaSpinner className="w-4 h-4 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    templateType === 'standard' ? 'Load Standard Template' : 'Create Blank Template'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

