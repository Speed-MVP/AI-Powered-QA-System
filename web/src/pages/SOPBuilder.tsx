import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle, FaSpinner, FaGripVertical, FaCheckCircle } from 'react-icons/fa'

interface FlowStep {
  id: string
  stage_id: string
  name: string
  description: string | null
  required: boolean
  expected_phrases: string[]
  timing_requirement: { enabled: boolean; seconds: number } | null
  order: number
}

interface FlowStage {
  id: string
  flow_version_id: string
  name: string
  order: number
  steps: FlowStep[]
}

interface FlowVersion {
  id: string
  company_id: string
  name: string
  description: string | null
  is_active: boolean
  version_number: number
  created_at: string
  updated_at: string
  stages: FlowStage[]
}

export function SOPBuilder() {
  const [flowVersions, setFlowVersions] = useState<FlowVersion[]>([])
  const [selectedFlowVersion, setSelectedFlowVersion] = useState<FlowVersion | null>(null)
  const [selectedStage, setSelectedStage] = useState<FlowStage | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showNewFlowVersion, setShowNewFlowVersion] = useState(false)
  const [newFlowVersionName, setNewFlowVersionName] = useState('')
  const [newFlowVersionDesc, setNewFlowVersionDesc] = useState('')
  const [editingStep, setEditingStep] = useState<FlowStep | null>(null)
  const [editingStage, setEditingStage] = useState<FlowStage | null>(null)
  const [showStageModal, setShowStageModal] = useState(false)
  const [showStepModal, setShowStepModal] = useState(false)
  const [showDeleteStageModal, setShowDeleteStageModal] = useState<FlowStage | null>(null)
  const [showDeleteStepModal, setShowDeleteStepModal] = useState<FlowStep | null>(null)
  const [showDeleteFlowVersionModal, setShowDeleteFlowVersionModal] = useState<FlowVersion | null>(null)
  const [showEditFlowVersionModal, setShowEditFlowVersionModal] = useState<FlowVersion | null>(null)
  const [editFlowVersionName, setEditFlowVersionName] = useState('')
  const [editFlowVersionDesc, setEditFlowVersionDesc] = useState('')
  const [newStageName, setNewStageName] = useState('')
  const [newStepName, setNewStepName] = useState('')
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templateType, setTemplateType] = useState<'blank' | 'standard'>('blank')
  const [loadingStandard, setLoadingStandard] = useState(false)

  useEffect(() => {
    loadFlowVersions()
  }, [])

  const loadFlowVersions = async () => {
    try {
      setLoading(true)
      setError(null)
      const versions = await api.listFlowVersions()
      setFlowVersions(versions)
      if (versions.length > 0 && !selectedFlowVersion) {
        setSelectedFlowVersion(versions[0])
        if (versions[0].stages.length > 0) {
          setSelectedStage(versions[0].stages[0])
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load flow versions')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadStandardTemplate = async () => {
    try {
      setLoadingStandard(true)
      setError(null)
      const response = await api.post('/api/templates/load-standard', {})
      
      // Close modal
      setShowTemplateModal(false)
      setTemplateType('blank')
      
      // Reload flow versions to get the new one
      await loadFlowVersions()
      
      // Select the newly created flow version (should be first in list since ordered by created_at desc)
      if (response.flow_version?.id) {
        // Find the new version in the reloaded list
        const versions = await api.listFlowVersions()
        const newVersion = versions.find(fv => fv.id === response.flow_version.id)
        if (newVersion) {
          setSelectedFlowVersion(newVersion)
          if (newVersion.stages?.length > 0) {
            setSelectedStage(newVersion.stages[0])
          }
        } else if (versions.length > 0) {
          // Fallback: select the first one (most recent)
          setSelectedFlowVersion(versions[0])
          if (versions[0].stages?.length > 0) {
            setSelectedStage(versions[0].stages[0])
          }
        }
      }
      
      // Show success message
      alert('Standard template loaded successfully!')
    } catch (err: any) {
      setError(err.message || 'Failed to load standard template')
    } finally {
      setLoadingStandard(false)
    }
  }

  const handleCreateFlowVersion = async () => {
    if (!newFlowVersionName.trim()) return

    try {
      setSaving(true)
      setError(null)
      const newVersion = await api.createFlowVersion({
        name: newFlowVersionName,
        description: newFlowVersionDesc || undefined,
      })
      await loadFlowVersions()
      setSelectedFlowVersion(newVersion as any)
      setNewFlowVersionName('')
      setNewFlowVersionDesc('')
      setShowNewFlowVersion(false)
    } catch (err: any) {
      setError(err.message || 'Failed to create flow version')
    } finally {
      setSaving(false)
    }
  }

  const handleEditFlowVersion = () => {
    if (!selectedFlowVersion) return
    setEditFlowVersionName(selectedFlowVersion.name)
    setEditFlowVersionDesc(selectedFlowVersion.description || '')
    setShowEditFlowVersionModal(selectedFlowVersion)
  }

  const confirmEditFlowVersion = async () => {
    if (!showEditFlowVersionModal || !editFlowVersionName.trim()) return

    try {
      setSaving(true)
      setError(null)
      await api.updateFlowVersion(showEditFlowVersionModal.id, {
        name: editFlowVersionName,
        description: editFlowVersionDesc || undefined,
      })
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === showEditFlowVersionModal.id)
      if (updated) {
        setSelectedFlowVersion(updated)
      }
      setShowEditFlowVersionModal(null)
      setEditFlowVersionName('')
      setEditFlowVersionDesc('')
    } catch (err: any) {
      setError(err.message || 'Failed to update flow version')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteFlowVersion = () => {
    if (!selectedFlowVersion) return
    setShowDeleteFlowVersionModal(selectedFlowVersion)
  }

  const confirmDeleteFlowVersion = async () => {
    if (!showDeleteFlowVersionModal) return

    try {
      setSaving(true)
      setError(null)
      await api.deleteFlowVersion(showDeleteFlowVersionModal.id)
      await loadFlowVersions()
      const remaining = flowVersions.filter(fv => fv.id !== showDeleteFlowVersionModal.id)
      if (remaining.length > 0) {
        setSelectedFlowVersion(remaining[0])
        setSelectedStage(remaining[0].stages[0] || null)
      } else {
        setSelectedFlowVersion(null)
        setSelectedStage(null)
      }
      setShowDeleteFlowVersionModal(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete flow version')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateStage = async () => {
    if (!selectedFlowVersion) return
    setNewStageName('')
    setShowStageModal(true)
  }

  const confirmCreateStage = async () => {
    if (!selectedFlowVersion || !newStageName.trim()) return

    try {
      setSaving(true)
      setError(null)
      const newStage = await api.createStage(selectedFlowVersion.id, {
        name: newStageName.trim(),
        order: selectedFlowVersion.stages.length + 1,
      })
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === selectedFlowVersion.id) || selectedFlowVersion
      const updatedStages = [...(updated.stages || []), newStage as any].sort((a, b) => a.order - b.order)
      setSelectedFlowVersion({ ...updated, stages: updatedStages })
      setSelectedStage(newStage as any)
      setShowStageModal(false)
      setNewStageName('')
    } catch (err: any) {
      setError(err.message || 'Failed to create stage')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateStep = async () => {
    if (!selectedFlowVersion || !selectedStage) return
    setNewStepName('')
    setShowStepModal(true)
  }

  const confirmCreateStep = async () => {
    if (!selectedFlowVersion || !selectedStage || !newStepName.trim()) return

    try {
      setSaving(true)
      setError(null)
      const newStep = await api.createStep(selectedFlowVersion.id, selectedStage.id, {
        name: newStepName.trim(),
        description: '',
        required: false,
        expected_phrases: [],
        timing_requirement: null,
        order: selectedStage.steps.length + 1,
      })
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === selectedFlowVersion.id) || selectedFlowVersion
      const updatedStages = updated.stages.map(s => 
        s.id === selectedStage.id 
          ? { ...s, steps: [...s.steps, newStep as any].sort((a, b) => a.order - b.order) }
          : s
      )
      setSelectedFlowVersion({ ...updated, stages: updatedStages })
      setSelectedStage(updatedStages.find(s => s.id === selectedStage.id) || null)
      setEditingStep(newStep as any)
      setShowStepModal(false)
      setNewStepName('')
    } catch (err: any) {
      setError(err.message || 'Failed to create step')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateStep = async (step: FlowStep, updates: Partial<FlowStep>) => {
    if (!selectedFlowVersion || !selectedStage) return

    try {
      setSaving(true)
      setError(null)
      await api.updateStep(selectedFlowVersion.id, selectedStage.id, step.id, updates)
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === selectedFlowVersion.id) || selectedFlowVersion
      const updatedStages = updated.stages.map(s => 
        s.id === selectedStage.id 
          ? { ...s, steps: s.steps.map(st => st.id === step.id ? { ...st, ...updates } : st) }
          : s
      )
      setSelectedFlowVersion({ ...updated, stages: updatedStages })
      setSelectedStage(updatedStages.find(s => s.id === selectedStage.id) || null)
      setEditingStep(null)
    } catch (err: any) {
      setError(err.message || 'Failed to update step')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteStep = async (step: FlowStep) => {
    if (!selectedFlowVersion || !selectedStage) return
    setShowDeleteStepModal(step)
  }

  const confirmDeleteStep = async () => {
    if (!selectedFlowVersion || !selectedStage || !showDeleteStepModal) return

    try {
      setSaving(true)
      setError(null)
      await api.deleteStep(selectedFlowVersion.id, selectedStage.id, showDeleteStepModal.id)
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === selectedFlowVersion.id) || selectedFlowVersion
      const updatedStages = updated.stages.map(s => 
        s.id === selectedStage.id 
          ? { ...s, steps: s.steps.filter(st => st.id !== showDeleteStepModal.id) }
          : s
      )
      setSelectedFlowVersion({ ...updated, stages: updatedStages })
      setSelectedStage(updatedStages.find(s => s.id === selectedStage.id) || null)
      setShowDeleteStepModal(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete step')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteStage = async (stage: FlowStage) => {
    if (!selectedFlowVersion) return
    setShowDeleteStageModal(stage)
  }

  const confirmDeleteStage = async () => {
    if (!selectedFlowVersion || !showDeleteStageModal) return

    try {
      setSaving(true)
      setError(null)
      await api.deleteStage(selectedFlowVersion.id, showDeleteStageModal.id)
      await loadFlowVersions()
      const updated = flowVersions.find(fv => fv.id === selectedFlowVersion.id) || selectedFlowVersion
      const updatedStages = updated.stages.filter(s => s.id !== showDeleteStageModal.id)
      setSelectedFlowVersion({ ...updated, stages: updatedStages })
      if (selectedStage?.id === showDeleteStageModal.id) {
        setSelectedStage(updatedStages.length > 0 ? updatedStages[0] : null)
      }
      setShowDeleteStageModal(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete stage')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading SOP Builder...</p>
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
                SOP Builder
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Define call flow stages and steps for quality evaluation
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedFlowVersion?.id || ''}
                onChange={(e) => {
                  const fv = flowVersions.find(v => v.id === e.target.value)
                  setSelectedFlowVersion(fv || null)
                  setSelectedStage(fv?.stages[0] || null)
                }}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                {flowVersions.map(fv => (
                  <option key={fv.id} value={fv.id}>
                    {fv.name} {fv.is_active && '✓'}
                  </option>
                ))}
              </select>
              {selectedFlowVersion && (
                <>
                  <button
                    onClick={handleEditFlowVersion}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                    title="Edit SOP"
                  >
                    <FaEdit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleDeleteFlowVersion}
                    className="px-3 py-2 border border-red-300 dark:border-red-600 rounded-md bg-white dark:bg-gray-800 text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                    title="Delete SOP"
                  >
                    <FaTrash className="w-4 h-4" />
                  </button>
                </>
              )}
              <button
                onClick={() => setShowTemplateModal(true)}
                className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 flex items-center gap-2"
              >
                <FaPlus className="w-4 h-4" />
                New SOP
              </button>
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

        {/* Template Selection Modal */}
        {showTemplateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Create New SOP
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
                          Start from scratch and build your own custom SOP
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
                    setShowTemplateModal(false)
                    setTemplateType('blank')
                    setError(null)
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    if (templateType === 'standard') {
                      await handleLoadStandardTemplate()
                    } else {
                      setShowTemplateModal(false)
                      setShowNewFlowVersion(true)
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
                    templateType === 'standard' ? 'Load Standard Template' : 'Create Blank SOP'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* New FlowVersion Form */}
        {showNewFlowVersion && (
          <div className="mb-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Create New SOP</h2>
              <button onClick={() => setShowNewFlowVersion(false)} className="text-gray-400 hover:text-gray-600">
                <FaTimes className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  SOP Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newFlowVersionName}
                  onChange={(e) => setNewFlowVersionName(e.target.value)}
                  placeholder="e.g., Customer Service Call Flow"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Description
                </label>
                <textarea
                  value={newFlowVersionDesc}
                  onChange={(e) => setNewFlowVersionDesc(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCreateFlowVersion}
                  disabled={saving || !newFlowVersionName.trim()}
                  className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaCheck className="w-4 h-4" />}
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowNewFlowVersion(false)
                    setNewFlowVersionName('')
                    setNewFlowVersionDesc('')
                  }}
                  className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {selectedFlowVersion ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Stages */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stages</h2>
                <button
                  onClick={handleCreateStage}
                  disabled={saving}
                  className="px-3 py-1.5 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 flex items-center gap-1.5 disabled:opacity-50"
                >
                  <FaPlus className="w-3 h-3" />
                  Add Stage
                </button>
              </div>
              <div className="p-4 space-y-2">
                {selectedFlowVersion.stages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p className="text-sm">No stages yet. Click "Add Stage" to create one.</p>
                  </div>
                ) : (
                  selectedFlowVersion.stages
                    .sort((a, b) => a.order - b.order)
                    .map((stage) => (
                      <div
                        key={stage.id}
                        onClick={() => setSelectedStage(stage)}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedStage?.id === stage.id
                            ? 'bg-brand-50 dark:bg-brand-900/20 border-brand-500'
                            : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 flex-1">
                            <FaGripVertical className="w-4 h-4 text-gray-400" />
                            <div>
                              <h3 className="font-medium text-gray-900 dark:text-white">{stage.name}</h3>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {stage.steps.length} {stage.steps.length === 1 ? 'step' : 'steps'}
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteStage(stage)
                            }}
                            className="p-1 text-red-600 hover:text-red-700"
                          >
                            <FaTrash className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    ))
                )}
              </div>
            </div>

            {/* Right Column - Steps */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              {selectedStage ? (
                <>
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Steps: {selectedStage.name}
                    </h2>
                    <button
                      onClick={handleCreateStep}
                      disabled={saving}
                      className="px-3 py-1.5 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <FaPlus className="w-3 h-3" />
                      Add Step
                    </button>
                  </div>
                  <div className="p-4 space-y-3">
                    {selectedStage.steps.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        <p className="text-sm">No steps yet. Click "Add Step" to create one.</p>
                      </div>
                    ) : (
                      selectedStage.steps
                        .sort((a, b) => a.order - b.order)
                        .map((step) =>
                          editingStep?.id === step.id ? (
                            <StepEditor
                              key={step.id}
                              step={step}
                              onSave={(updates) => handleUpdateStep(step, updates)}
                              onCancel={() => setEditingStep(null)}
                            />
                          ) : (
                            <div
                              key={step.id}
                              className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <FaGripVertical className="w-3 h-3 text-gray-400" />
                                    <h4 className="font-medium text-gray-900 dark:text-white">{step.name}</h4>
                                    {step.required && (
                                      <span className="px-1.5 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs rounded">
                                        Required
                                      </span>
                                    )}
                                  </div>
                                  {step.description && (
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{step.description}</p>
                                  )}
                                  {step.expected_phrases.length > 0 && (
                                    <div className="text-xs text-gray-500 dark:text-gray-400">
                                      Phrases: {step.expected_phrases.join(', ')}
                                    </div>
                                  )}
                                  {step.timing_requirement?.enabled && (
                                    <div className="text-xs text-gray-500 dark:text-gray-400">
                                      Timing: {step.timing_requirement.seconds}s
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => setEditingStep(step)}
                                    className="p-1 text-brand-600 hover:text-brand-700"
                                  >
                                    <FaEdit className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={() => handleDeleteStep(step)}
                                    className="p-1 text-red-600 hover:text-red-700"
                                  >
                                    <FaTrash className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          )
                        )
                    )}
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  <p className="text-sm">Select a stage to view its steps</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-4">No SOP selected. Create a new one to get started.</p>
            <button
              onClick={() => setShowNewFlowVersion(true)}
              className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700"
            >
              Create SOP
            </button>
          </div>
        )}

        {/* Stage Creation Modal */}
        {showStageModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Create New Stage
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Stage Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newStageName}
                    onChange={(e) => setNewStageName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newStageName.trim()) {
                        confirmCreateStage()
                      }
                    }}
                    placeholder="e.g., Opening, Discovery, Resolution"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                </div>
                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => {
                      setShowStageModal(false)
                      setNewStageName('')
                    }}
                    disabled={saving}
                    className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmCreateStage}
                    disabled={saving || !newStageName.trim()}
                    className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaCheck className="w-4 h-4" />}
                    Create
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step Creation Modal */}
        {showStepModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Create New Step
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Step Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newStepName}
                    onChange={(e) => setNewStepName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newStepName.trim()) {
                        confirmCreateStep()
                      }
                    }}
                    placeholder="e.g., Greet customer, Verify identity"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                </div>
                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => {
                      setShowStepModal(false)
                      setNewStepName('')
                    }}
                    disabled={saving}
                    className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmCreateStep}
                    disabled={saving || !newStepName.trim()}
                    className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaCheck className="w-4 h-4" />}
                    Create
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Stage Confirmation Modal */}
        {showDeleteStageModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Delete Stage
              </h3>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-6">
                Are you sure you want to delete the stage <strong>"{showDeleteStageModal.name}"</strong> and all its steps? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowDeleteStageModal(null)}
                  disabled={saving}
                  className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteStage}
                  disabled={saving}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaTrash className="w-4 h-4" />}
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Step Confirmation Modal */}
        {showDeleteStepModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Delete Step
              </h3>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-6">
                Are you sure you want to delete the step <strong>"{showDeleteStepModal.name}"</strong>? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowDeleteStepModal(null)}
                  disabled={saving}
                  className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteStep}
                  disabled={saving}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaTrash className="w-4 h-4" />}
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit FlowVersion Modal */}
        {showEditFlowVersionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Edit SOP</h2>
              </div>
              <div className="p-6 space-y-4">
                {error && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
                    {error}
                  </div>
                )}
                <div>
                  <label htmlFor="editFlowVersionName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    SOP Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="editFlowVersionName"
                    value={editFlowVersionName}
                    onChange={(e) => setEditFlowVersionName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Customer Service Call Flow"
                    autoFocus
                  />
                </div>
                <div>
                  <label htmlFor="editFlowVersionDesc" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    id="editFlowVersionDesc"
                    value={editFlowVersionDesc}
                    onChange={(e) => setEditFlowVersionDesc(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional description"
                  />
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditFlowVersionModal(null)
                    setEditFlowVersionName('')
                    setEditFlowVersionDesc('')
                    setError(null)
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmEditFlowVersion}
                  disabled={saving || !editFlowVersionName.trim()}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSave className="w-4 h-4" />}
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete FlowVersion Confirmation Modal */}
        {showDeleteFlowVersionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Delete SOP</h2>
              </div>
              <div className="p-6 space-y-4">
                {error && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
                    {error}
                  </div>
                )}
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  Are you sure you want to delete the SOP <strong className="text-gray-900 dark:text-white">"{showDeleteFlowVersionModal.name}"</strong>?
                </p>
                <p className="text-sm text-red-600 dark:text-red-400">
                  This will permanently delete the SOP and all its stages and steps. This action cannot be undone.
                </p>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteFlowVersionModal(null)
                    setError(null)
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDeleteFlowVersion}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaTrash className="w-4 h-4" />}
                  Delete SOP
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function StepEditor({
  step,
  onSave,
  onCancel,
}: {
  step: FlowStep
  onSave: (updates: Partial<FlowStep>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(step.name)
  const [description, setDescription] = useState(step.description || '')
  const [required, setRequired] = useState(step.required)
  const [expectedPhrases, setExpectedPhrases] = useState(step.expected_phrases.join(', '))
  const [timingEnabled, setTimingEnabled] = useState(step.timing_requirement?.enabled || false)
  const [timingSeconds, setTimingSeconds] = useState(step.timing_requirement?.seconds || 0)

  const handleSave = () => {
    onSave({
      name,
      description: description || null,
      required,
      expected_phrases: expectedPhrases.split(',').map(p => p.trim()).filter(p => p),
      timing_requirement: timingEnabled ? { enabled: true, seconds: timingSeconds } : null,
    })
  }

  return (
    <div className="p-4 bg-white dark:bg-gray-800 border border-brand-500 rounded-lg">
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Step Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="required"
            checked={required}
            onChange={(e) => setRequired(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="required" className="text-sm text-gray-700 dark:text-gray-300">
            Required Step
          </label>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Expected Phrases (comma-separated)
          </label>
          <input
            type="text"
            value={expectedPhrases}
            onChange={(e) => setExpectedPhrases(e.target.value)}
            placeholder="e.g., hello, thank you, goodbye"
            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="timing"
              checked={timingEnabled}
              onChange={(e) => setTimingEnabled(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="timing" className="text-sm text-gray-700 dark:text-gray-300">
              Timing Requirement
            </label>
          </div>
          {timingEnabled && (
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Must occur within (seconds)
              </label>
              <input
                type="number"
                value={timingSeconds}
                onChange={(e) => setTimingSeconds(parseInt(e.target.value) || 0)}
                min="0"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          )}
        </div>
        <div className="flex gap-2 pt-2">
          <button
            onClick={handleSave}
            className="px-3 py-1.5 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 flex items-center gap-1.5"
          >
            <FaSave className="w-3 h-3" />
            Save
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-md"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

