import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle, FaSpinner, FaCheckCircle, FaGripVertical, FaChevronDown, FaChevronUp } from 'react-icons/fa'
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

interface RubricCategory {
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
    target_type: 'stage' | 'step'
    target_id: string
    contribution_weight: number
    required_flag: boolean
  }>
}

interface RubricTemplate {
  id: string
  policy_template_id: string | null
  flow_version_id: string
  name: string
  description: string | null
  version_number: number
  is_active: boolean
  created_at: string
  categories: RubricCategory[]
}

export function RubricBuilder() {
  const [flowVersions, setFlowVersions] = useState<FlowVersion[]>([])
  const [selectedFlowVersion, setSelectedFlowVersion] = useState<FlowVersion | null>(null)
  const [rubrics, setRubrics] = useState<RubricTemplate[]>([])
  const [selectedRubric, setSelectedRubric] = useState<RubricTemplate | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<RubricCategory | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [showMappingModal, setShowMappingModal] = useState(false)
  const [mappingsVisible, setMappingsVisible] = useState(true)
  const [editingRubric, setEditingRubric] = useState<RubricTemplate | null>(null)
  const [editingCategory, setEditingCategory] = useState<RubricCategory | null>(null)
  const [deleteConfirmModal, setDeleteConfirmModal] = useState<{ type: 'rubric' | 'category' | 'mapping'; item: any; onConfirm: () => void } | null>(null)

  // Form state
  const [rubricName, setRubricName] = useState('')
  const [rubricDescription, setRubricDescription] = useState('')
  const [categoryName, setCategoryName] = useState('')
  const [categoryDescription, setCategoryDescription] = useState('')
  const [categoryWeight, setCategoryWeight] = useState(0)
  const [categoryPassThreshold, setCategoryPassThreshold] = useState(75)
  const [levelDefinitions, setLevelDefinitions] = useState<Array<{ name: string; min_score: number; max_score: number; description?: string; label?: string }>>([])
  const [mappingRows, setMappingRows] = useState<Array<{
    target_type: 'stage' | 'step'
    target_id: string
    contribution_weight: number
    required_flag: boolean
  }>>([{ target_type: 'step', target_id: '', contribution_weight: 1.0, required_flag: false }])

  useEffect(() => {
    loadFlowVersions()
  }, [])

  useEffect(() => {
    if (selectedFlowVersion) {
      loadRubrics()
    }
  }, [selectedFlowVersion])

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

  const loadRubrics = async () => {
    if (!selectedFlowVersion) return
    try {
      setLoading(true)
      const rubricsData = await api.listRubrics({ flow_version_id: selectedFlowVersion.id })
      setRubrics(rubricsData as any)
      if (rubricsData.length > 0 && !selectedRubric) {
        setSelectedRubric(rubricsData[0] as any)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load rubrics')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRubric = () => {
    setEditingRubric(null)
    setRubricName('')
    setRubricDescription('')
    setShowRubricModal(true)
  }

  const handleEditRubric = (rubric: RubricTemplate) => {
    setEditingRubric(rubric)
    setRubricName(rubric.name)
    setRubricDescription(rubric.description || '')
    setShowRubricModal(true)
  }

  const handleSaveRubric = async () => {
    if (!selectedFlowVersion || !rubricName.trim()) {
      setError('Rubric name is required')
      return
    }

    try {
      setSaving(true)
      setError(null)

      if (editingRubric) {
        await api.updateRubric(editingRubric.id, {
          name: rubricName.trim(),
          description: rubricDescription.trim() || undefined,
        })
      } else {
        await api.createRubric({
          flow_version_id: selectedFlowVersion.id,
          name: rubricName.trim(),
          description: rubricDescription.trim() || undefined,
        })
      }

      await loadRubrics()
      setShowRubricModal(false)
      resetRubricForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save rubric')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRubric = (rubric: RubricTemplate) => {
    setDeleteConfirmModal({
      type: 'rubric',
      item: rubric,
      onConfirm: async () => {
        setDeleteConfirmModal(null)
        try {
          setSaving(true)
          await api.deleteRubric(rubric.id)
          await loadRubrics()
          if (selectedRubric?.id === rubric.id) {
            setSelectedRubric(null)
            setSelectedCategory(null)
          }
        } catch (err: any) {
          setError(err.message || 'Failed to delete rubric')
        } finally {
          setSaving(false)
        }
      },
    })
  }

  const handlePublishRubric = async (rubric: RubricTemplate) => {
    try {
      setSaving(true)
      await api.publishRubric(rubric.id)
      await loadRubrics()
    } catch (err: any) {
      setError(err.message || 'Failed to publish rubric')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateCategory = () => {
    if (!selectedRubric) return
    setEditingCategory(null)
    setCategoryName('')
    setCategoryDescription('')
    setCategoryWeight(0)
    setCategoryPassThreshold(75)
    setLevelDefinitions([
      { name: 'Excellent', min_score: 90, max_score: 100, description: '', label: 'Exceeds' },
      { name: 'Good', min_score: 75, max_score: 89, description: '', label: 'Meets' },
      { name: 'Fair', min_score: 60, max_score: 74, description: '', label: 'Partially Meets' },
      { name: 'Poor', min_score: 0, max_score: 59, description: '', label: 'Does Not Meet' },
    ])
    setShowCategoryModal(true)
  }

  const handleEditCategory = (category: RubricCategory) => {
    setEditingCategory(category)
    setCategoryName(category.name)
    setCategoryDescription(category.description || '')
    setCategoryWeight(category.weight)
    setCategoryPassThreshold(category.pass_threshold)
    setLevelDefinitions(category.level_definitions || [])
    setShowCategoryModal(true)
  }

  const handleSaveCategory = async () => {
    if (!selectedRubric || !categoryName.trim()) {
      setError('Category name is required')
      return
    }

    try {
      setSaving(true)
      setError(null)

      if (editingCategory) {
        await api.updateRubricCategory(selectedRubric.id, editingCategory.id, {
          name: categoryName.trim(),
          description: categoryDescription.trim() || undefined,
          weight: categoryWeight,
          pass_threshold: categoryPassThreshold,
          level_definitions: levelDefinitions,
        })
      } else {
        await api.createRubricCategory(selectedRubric.id, {
          name: categoryName.trim(),
          description: categoryDescription.trim() || undefined,
          weight: categoryWeight,
          pass_threshold: categoryPassThreshold,
          level_definitions: levelDefinitions,
        })
      }

      // Reload rubrics and restore selection
      const rubricsData = await api.listRubrics({ flow_version_id: selectedFlowVersion!.id })
      setRubrics(rubricsData as any)
      
      // Restore selected rubric with updated categories
      const restoredRubric = rubricsData.find((r: any) => r.id === selectedRubric.id)
      if (restoredRubric) {
        setSelectedRubric(restoredRubric as any)
        // If editing, restore the edited category; if creating, select the new one
        if (editingCategory) {
          const restoredCategory = restoredRubric.categories?.find((c: any) => c.id === editingCategory.id)
          if (restoredCategory) {
            setSelectedCategory(restoredCategory as any)
            setMappingsVisible(true)
          }
        } else {
          // Select the newly created category (last one in the list)
          const newCategory = restoredRubric.categories?.[restoredRubric.categories.length - 1]
          if (newCategory) {
            setSelectedCategory(newCategory as any)
            setMappingsVisible(true) // Show mappings section for new category
          }
        }
      } else if (rubricsData.length > 0) {
        setSelectedRubric(rubricsData[0] as any)
        setSelectedCategory(null)
      }
      
      setShowCategoryModal(false)
      resetCategoryForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save category')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteCategory = (category: RubricCategory) => {
    if (!selectedRubric) return
    setDeleteConfirmModal({
      type: 'category',
      item: category,
      onConfirm: async () => {
        setDeleteConfirmModal(null)
        try {
          setSaving(true)
          await api.deleteRubricCategory(selectedRubric.id, category.id)
          await loadRubrics()
          if (selectedCategory?.id === category.id) {
            setSelectedCategory(null)
          }
        } catch (err: any) {
          setError(err.message || 'Failed to delete category')
        } finally {
          setSaving(false)
        }
      },
    })
  }

  const handleCreateMapping = () => {
    if (!selectedRubric || !selectedCategory) return
    setMappingRows([{ target_type: 'step', target_id: '', contribution_weight: 1.0, required_flag: false }])
    setShowMappingModal(true)
  }

  const handleSaveMapping = async () => {
    if (!selectedRubric || !selectedCategory) {
      setError('Please select a rubric and category')
      return
    }

    if (!mappingRows || mappingRows.length === 0) {
      setError('Please add at least one mapping')
      return
    }

    // Validate all rows have targets
    const invalidRows = mappingRows.filter(row => !row.target_id)
    if (invalidRows.length > 0) {
      setError('Please select a target for all mappings')
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      // Save all mappings
      await Promise.all(
        mappingRows.map(row =>
          api.createRubricMapping(selectedRubric.id, selectedCategory.id, {
            target_type: row.target_type,
            target_id: row.target_id,
            contribution_weight: row.contribution_weight,
            required_flag: row.required_flag,
          })
        )
      )
      
      // Reload rubrics and restore selection
      const rubricsData = await api.listRubrics({ flow_version_id: selectedFlowVersion!.id })
      setRubrics(rubricsData as any)
      
      // Restore selected rubric and category with updated mappings
      const restoredRubric = rubricsData.find((r: any) => r.id === selectedRubric.id)
      if (restoredRubric) {
        setSelectedRubric(restoredRubric as any)
        const restoredCategory = restoredRubric.categories?.find((c: any) => c.id === selectedCategory.id)
        if (restoredCategory) {
          // Update the category with fresh data including new mappings
          setSelectedCategory(restoredCategory as any)
        } else {
          setSelectedCategory(null)
        }
      } else if (rubricsData.length > 0) {
        setSelectedRubric(rubricsData[0] as any)
        setSelectedCategory(null)
      }
      
      setShowMappingModal(false)
      resetMappingForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save mappings')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteMapping = (mappingId: string) => {
    if (!selectedRubric || !selectedCategory) return
    setDeleteConfirmModal({
      type: 'mapping',
      item: { id: mappingId },
      onConfirm: async () => {
        setDeleteConfirmModal(null)
        try {
          setSaving(true)
          await api.deleteRubricMapping(selectedRubric.id, selectedCategory.id, mappingId)
          await loadRubrics()
        } catch (err: any) {
          setError(err.message || 'Failed to delete mapping')
        } finally {
          setSaving(false)
        }
      },
    })
  }

  const resetRubricForm = () => {
    setEditingRubric(null)
    setRubricName('')
    setRubricDescription('')
  }

  const resetCategoryForm = () => {
    setEditingCategory(null)
    setCategoryName('')
    setCategoryDescription('')
    setCategoryWeight(0)
    setCategoryPassThreshold(75)
    setLevelDefinitions([])
  }

  const resetMappingForm = () => {
    setMappingRows([{ target_type: 'step', target_id: '', contribution_weight: 1.0, required_flag: false }])
  }

  const getTotalWeight = () => {
    if (!selectedRubric) return 0
    return selectedRubric.categories.reduce((sum, cat) => sum + cat.weight, 0)
  }

  const getTargetName = (targetType: string, targetId: string) => {
    if (!selectedFlowVersion) return targetId
    if (targetType === 'stage') {
      return selectedFlowVersion.stages.find(s => s.id === targetId)?.name || targetId
    } else {
      return selectedFlowVersion.stages.flatMap(s => s.steps).find(s => s.id === targetId)?.name || targetId
    }
  }

  if (loading && flowVersions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading Rubric Builder...</p>
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
                Rubric Builder
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Define scoring categories and map them to SOP stages/steps
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedFlowVersion?.id || ''}
                onChange={(e) => {
                  const fv = flowVersions.find(v => v.id === e.target.value)
                  setSelectedFlowVersion(fv || null)
                  setSelectedRubric(null)
                  setSelectedCategory(null)
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
                  onClick={handleCreateRubric}
                  className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700 flex items-center gap-2"
                >
                  <FaPlus className="w-4 h-4" />
                  New Rubric
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Rubrics List */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Rubrics ({rubrics.length})
                </h2>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
                {rubrics.length === 0 ? (
                  <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400 text-sm">
                    No rubrics defined. Click "New Rubric" to create one.
                  </div>
                ) : (
                  rubrics.map(rubric => (
                    <div
                      key={rubric.id}
                      onClick={() => {
                        setSelectedRubric(rubric)
                        setSelectedCategory(null)
                      }}
                      className={`px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                        selectedRubric?.id === rubric.id ? 'bg-brand-50 dark:bg-brand-900/20' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                            {rubric.name}
                          </h3>
                          {rubric.is_active && (
                            <span className="inline-flex items-center gap-1 mt-1 text-xs text-green-600 dark:text-green-400">
                              <FaCheckCircle className="w-3 h-3" />
                              Active
                            </span>
                          )}
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {rubric.categories.length} categories
                          </p>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleEditRubric(rubric)
                            }}
                            className="p-1 text-gray-400 hover:text-brand-600 dark:hover:text-brand-400"
                            title="Edit"
                          >
                            <FaEdit className="w-3 h-3" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteRubric(rubric)
                            }}
                            className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                            title="Delete"
                          >
                            <FaTrash className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Categories and Mappings */}
          <div className="lg:col-span-2">
            {selectedRubric ? (
              <div className="space-y-6">
                {/* Rubric Header */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        {selectedRubric.name}
                      </h2>
                      {selectedRubric.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {selectedRubric.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {!selectedRubric.is_active && (
                        <button
                          onClick={() => handlePublishRubric(selectedRubric)}
                          disabled={getTotalWeight() !== 100}
                          className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                          title={getTotalWeight() !== 100 ? 'Category weights must sum to 100%' : 'Publish rubric'}
                        >
                          <FaCheckCircle className="w-4 h-4" />
                          Publish
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      Total Weight: <strong className={getTotalWeight() === 100 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                        {getTotalWeight().toFixed(1)}%
                      </strong>
                    </span>
                    {getTotalWeight() !== 100 && (
                      <span className="text-red-600 dark:text-red-400 text-xs">
                        Weights must sum to 100%
                      </span>
                    )}
                  </div>
                </div>

                {/* Categories Grid */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Categories ({selectedRubric.categories.length})
                    </h3>
                    <button
                      onClick={handleCreateCategory}
                      className="px-3 py-1.5 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 flex items-center gap-2"
                    >
                      <FaPlus className="w-3 h-3" />
                      Add Category
                    </button>
                  </div>
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {selectedRubric.categories.length === 0 ? (
                      <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
                        No categories defined. Click "Add Category" to create one.
                      </div>
                    ) : (
                      selectedRubric.categories.map(category => (
                        <div
                          key={category.id}
                          onClick={() => {
                            setSelectedCategory(category)
                            setMappingsVisible(true)
                          }}
                          className={`px-6 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                            selectedCategory?.id === category.id ? 'bg-brand-50 dark:bg-brand-900/20' : ''
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h4 className="text-base font-medium text-gray-900 dark:text-white">
                                  {category.name}
                                </h4>
                                <span className="px-2 py-1 text-xs font-medium rounded bg-brand-100 text-brand-800 dark:bg-brand-900/20 dark:text-brand-400">
                                  {category.weight}%
                                </span>
                                <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                                  Pass: {category.pass_threshold}%
                                </span>
                              </div>
                              {category.description && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                  {category.description}
                                </p>
                              )}
                              <div className="flex items-center gap-3 mt-2">
                                <p className="text-xs text-gray-500 dark:text-gray-500">
                                  {category.mappings.length} mapping(s)
                                </p>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setSelectedCategory(category)
                                    setMappingsVisible(true)
                                    handleCreateMapping()
                                  }}
                                  className="px-2.5 py-1 text-xs font-medium bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400 rounded-md hover:bg-brand-100 dark:hover:bg-brand-900/30 flex items-center gap-1.5 transition-colors"
                                  title="Add mapping to this category"
                                >
                                  <FaPlus className="w-3 h-3" />
                                  Add Mapping
                                </button>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleEditCategory(category)
                                }}
                                className="p-1.5 text-gray-400 hover:text-brand-600 dark:hover:text-brand-400"
                                title="Edit"
                              >
                                <FaEdit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDeleteCategory(category)
                                }}
                                className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
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

                {/* Category Mappings */}
                {selectedCategory && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow border-2 border-dashed border-gray-300 dark:border-gray-600">
                    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-800">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              Stage/Step Mappings
                            </h3>
                            <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300">
                              {selectedCategory.mappings.length}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Map stages or steps from your SOP to this category: <span className="font-medium text-gray-900 dark:text-white">{selectedCategory.name}</span>
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setMappingsVisible(!mappingsVisible)}
                            className="px-3 py-2 text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 border border-gray-300 dark:border-gray-600 transition-all flex items-center gap-2"
                            title={mappingsVisible ? "Hide mappings" : "Show mappings"}
                          >
                            {mappingsVisible ? (
                              <>
                                <FaChevronUp className="w-3 h-3" />
                                Hide
                              </>
                            ) : (
                              <>
                                <FaChevronDown className="w-3 h-3" />
                                Show
                              </>
                            )}
                          </button>
                          <button
                            onClick={handleCreateMapping}
                            className="px-4 py-2.5 text-sm font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 shadow-md hover:shadow-lg transition-all flex items-center gap-2 whitespace-nowrap"
                          >
                            <FaPlus className="w-4 h-4" />
                            Add Mapping
                          </button>
                        </div>
                      </div>
                    </div>
                    {mappingsVisible && (
                    <div className="divide-y divide-gray-200 dark:divide-gray-700">
                      {selectedCategory.mappings.length === 0 ? (
                        <div className="px-6 py-16 text-center">
                          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-100 dark:bg-brand-900/20 mb-4">
                            <FaPlus className="w-8 h-8 text-brand-600 dark:text-brand-400" />
                          </div>
                          <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                            No mappings yet
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 max-w-sm mx-auto">
                            Map stages or steps from your SOP flow to this category to define how they contribute to scoring.
                          </p>
                          <button
                            onClick={handleCreateMapping}
                            className="px-5 py-2.5 text-sm font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 shadow-md hover:shadow-lg transition-all flex items-center gap-2 mx-auto"
                          >
                            <FaPlus className="w-4 h-4" />
                            Add Your First Mapping
                          </button>
                        </div>
                      ) : (
                        <>
                          {selectedCategory.mappings.map(mapping => (
                            <div key={mapping.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-3 mb-1">
                                    <span className="px-2.5 py-1 text-xs font-medium rounded bg-brand-100 text-brand-800 dark:bg-brand-900/20 dark:text-brand-400">
                                      {mapping.target_type}
                                    </span>
                                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                                      {getTargetName(mapping.target_type, mapping.target_id)}
                                    </span>
                                    {mapping.required_flag && (
                                      <span className="px-2.5 py-1 text-xs font-medium rounded bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                                        Required
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Weight: {mapping.contribution_weight}x
                                  </p>
                                </div>
                                <button
                                  onClick={() => handleDeleteMapping(mapping.id)}
                                  className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded transition-colors"
                                  title="Delete mapping"
                                >
                                  <FaTrash className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          ))}
                          <div className="px-6 py-4 border-t-2 border-dashed border-gray-300 dark:border-gray-600">
                            <button
                              onClick={handleCreateMapping}
                              className="w-full px-4 py-2.5 text-sm font-medium bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400 rounded-lg hover:bg-brand-100 dark:hover:bg-brand-900/30 border-2 border-dashed border-brand-300 dark:border-brand-700 transition-all flex items-center justify-center gap-2"
                            >
                              <FaPlus className="w-4 h-4" />
                              Add Another Mapping
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
                <p className="text-gray-500 dark:text-gray-400">
                  Select a rubric from the list to view and edit categories
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Rubric Modal */}
        {showRubricModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {editingRubric ? 'Edit Rubric' : 'Create Rubric'}
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={rubricName}
                    onChange={(e) => setRubricName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g., Customer Service Rubric"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={rubricDescription}
                    onChange={(e) => setRubricDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowRubricModal(false)
                    resetRubricForm()
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveRubric}
                  disabled={saving || !rubricName.trim()}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSave className="w-4 h-4" />}
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Category Modal */}
        {showCategoryModal && selectedRubric && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full my-8">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {editingCategory ? 'Edit Category' : 'Create Category'}
                </h2>
              </div>
              <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={categoryName}
                      onChange={(e) => setCategoryName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Weight (%) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={categoryWeight}
                      onChange={(e) => setCategoryWeight(parseFloat(e.target.value) || 0)}
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description <span className="text-gray-500 text-xs">(Important: Explain what this category evaluates)</span>
                  </label>
                  <textarea
                    value={categoryDescription}
                    onChange={(e) => setCategoryDescription(e.target.value)}
                    rows={4}
                    placeholder="Describe what this category evaluates and how it should be scored. This helps reviewers understand the category's purpose and scoring criteria."
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Pass Threshold (%)
                  </label>
                  <input
                    type="number"
                    value={categoryPassThreshold}
                    onChange={(e) => setCategoryPassThreshold(parseInt(e.target.value) || 75)}
                    min="0"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Level Definitions
                  </label>
                  <div className="space-y-3">
                    {levelDefinitions.map((level, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg space-y-2">
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={level.name}
                            onChange={(e) => {
                              const updated = [...levelDefinitions]
                              updated[idx].name = e.target.value
                              setLevelDefinitions(updated)
                            }}
                            placeholder="Level name (e.g., Excellent)"
                            className="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                          <input
                            type="text"
                            inputMode="numeric"
                            value={level.min_score === 0 ? '0' : level.min_score || ''}
                            onChange={(e) => {
                              const updated = [...levelDefinitions]
                              const val = e.target.value.trim()
                              if (val === '') {
                                // Allow empty while typing
                                updated[idx].min_score = 0
                              } else {
                                const num = parseInt(val)
                                if (!isNaN(num)) {
                                  updated[idx].min_score = Math.max(0, Math.min(100, num))
                                } else {
                                  // Keep current value if invalid
                                  updated[idx].min_score = level.min_score
                                }
                              }
                              setLevelDefinitions(updated)
                            }}
                            onBlur={(e) => {
                              // Set to 0 if empty on blur
                              if (e.target.value === '') {
                                const updated = [...levelDefinitions]
                                updated[idx].min_score = 0
                                setLevelDefinitions(updated)
                              }
                            }}
                            placeholder="Min"
                            className="w-20 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                          <input
                            type="text"
                            inputMode="numeric"
                            value={level.max_score === 0 ? '0' : level.max_score || ''}
                            onChange={(e) => {
                              const updated = [...levelDefinitions]
                              const val = e.target.value.trim()
                              if (val === '') {
                                // Allow empty while typing
                                updated[idx].max_score = 0
                              } else {
                                const num = parseInt(val)
                                if (!isNaN(num)) {
                                  updated[idx].max_score = Math.max(0, Math.min(100, num))
                                } else {
                                  // Keep current value if invalid
                                  updated[idx].max_score = level.max_score
                                }
                              }
                              setLevelDefinitions(updated)
                            }}
                            onBlur={(e) => {
                              // Set to 0 if empty on blur
                              if (e.target.value === '') {
                                const updated = [...levelDefinitions]
                                updated[idx].max_score = 0
                                setLevelDefinitions(updated)
                              }
                            }}
                            placeholder="Max"
                            className="w-20 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                          <button
                            onClick={() => {
                              setLevelDefinitions(levelDefinitions.filter((_, i) => i !== idx))
                            }}
                            className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                            title="Delete level"
                          >
                            <FaTrash className="w-4 h-4" />
                          </button>
                        </div>
                        <textarea
                          value={level.description || ''}
                          onChange={(e) => {
                            const updated = [...levelDefinitions]
                            updated[idx].description = e.target.value
                            setLevelDefinitions(updated)
                          }}
                          placeholder="Describe what this performance level means (e.g., 'All requirements met perfectly, exceeds expectations')"
                          rows={2}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                        />
                      </div>
                    ))}
                    <button
                      onClick={() => {
                        setLevelDefinitions([...levelDefinitions, { name: '', min_score: 0, max_score: 0, description: '' }])
                      }}
                      className="w-full px-3 py-2 text-sm border border-dashed border-gray-300 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <FaPlus className="w-3 h-3 inline mr-1" />
                      Add Level
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowCategoryModal(false)
                    resetCategoryForm()
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveCategory}
                  disabled={saving || !categoryName.trim()}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSave className="w-4 h-4" />}
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Mapping Modal */}
        {showMappingModal && selectedRubric && selectedCategory && selectedFlowVersion && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Add Mappings
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Add multiple stage/step mappings to category: <span className="font-medium">{selectedCategory.name}</span>
                </p>
              </div>
              <div className="p-6 overflow-y-auto flex-1">
                <div className="space-y-4">
                  {mappingRows.map((row, idx) => (
                    <div key={idx} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700/30 space-y-3">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Mapping {idx + 1}
                        </h3>
                        {mappingRows.length > 1 && (
                          <button
                            onClick={() => {
                              setMappingRows(mappingRows.filter((_, i) => i !== idx))
                            }}
                            className="p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                            title="Remove mapping"
                          >
                            <FaTrash className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Target Type
                          </label>
                          <select
                            value={row.target_type}
                            onChange={(e) => {
                              const updated = [...mappingRows]
                              updated[idx].target_type = e.target.value as 'stage' | 'step'
                              updated[idx].target_id = '' // Reset target when type changes
                              setMappingRows(updated)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="stage">Stage</option>
                            <option value="step">Step</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Target <span className="text-red-500">*</span>
                          </label>
                          <select
                            value={row.target_id}
                            onChange={(e) => {
                              const updated = [...mappingRows]
                              updated[idx].target_id = e.target.value
                              setMappingRows(updated)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">Select {row.target_type}...</option>
                            {selectedFlowVersion && (
                              row.target_type === 'stage'
                                ? selectedFlowVersion.stages.map(stage => (
                                    <option key={stage.id} value={stage.id}>
                                      {stage.name}
                                    </option>
                                  ))
                                : selectedFlowVersion.stages.flatMap(s => s.steps).map(step => (
                                    <option key={step.id} value={step.id}>
                                      {step.name}
                                    </option>
                                  ))
                            )}
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Contribution Weight
                          </label>
                          <input
                            type="number"
                            value={row.contribution_weight}
                            onChange={(e) => {
                              const updated = [...mappingRows]
                              updated[idx].contribution_weight = parseFloat(e.target.value) || 1.0
                              setMappingRows(updated)
                            }}
                            min="0"
                            step="0.1"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div className="flex items-end">
                          <div className="flex items-center gap-2 w-full">
                            <input
                              type="checkbox"
                              id={`mappingRequired-${idx}`}
                              checked={row.required_flag}
                              onChange={(e) => {
                                const updated = [...mappingRows]
                                updated[idx].required_flag = e.target.checked
                                setMappingRows(updated)
                              }}
                              className="w-4 h-4"
                            />
                            <label htmlFor={`mappingRequired-${idx}`} className="text-sm text-gray-700 dark:text-gray-300">
                              Required (critical to category)
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      setMappingRows([...mappingRows, { target_type: 'step', target_id: '', contribution_weight: 1.0, required_flag: false }])
                    }}
                    className="w-full px-4 py-2 text-sm border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 flex items-center justify-center gap-2 transition-colors"
                  >
                    <FaPlus className="w-4 h-4" />
                    Add Another Mapping
                  </button>
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowMappingModal(false)
                    resetMappingForm()
                  }}
                  disabled={saving}
                  className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveMapping}
                  disabled={saving || !mappingRows || mappingRows.length === 0 || mappingRows.some(r => !r.target_id)}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSave className="w-4 h-4" />}
                  Save {mappingRows?.length || 0} Mapping{(mappingRows?.length || 0) !== 1 ? 's' : ''}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteConfirmModal && (
          <ConfirmModal
            isOpen={deleteConfirmModal.isOpen}
            onClose={() => setDeleteConfirmModal(null)}
            onConfirm={deleteConfirmModal.onConfirm}
            title={`Delete ${deleteConfirmModal.type === 'rubric' ? 'Rubric' : deleteConfirmModal.type === 'category' ? 'Category' : 'Mapping'}`}
            message={
              deleteConfirmModal.type === 'rubric'
                ? `Delete rubric "${deleteConfirmModal.item.name}"? This will delete all categories and mappings.`
                : deleteConfirmModal.type === 'category'
                ? `Delete category "${deleteConfirmModal.item.name}"?`
                : 'Delete this mapping?'
            }
            confirmText="Delete"
            cancelText="Cancel"
            confirmColor="red"
            danger
            loading={saving}
          />
        )}
      </div>
    </div>
  )
}

