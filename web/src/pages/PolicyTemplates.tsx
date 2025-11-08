import { useState } from 'react'
import { usePolicyStore, type EvaluationCriteria } from '@/store/policyStore'
import { FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaCheck, FaExclamationCircle } from 'react-icons/fa'

export function PolicyTemplates() {
  const {
    templates,
    activeTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    setActiveTemplate,
    addCriteria,
    updateCriteria,
    deleteCriteria,
  } = usePolicyStore()

  const [editingTemplate, setEditingTemplate] = useState<string | null>(null)
  const [editingCriteria, setEditingCriteria] = useState<string | null>(null)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [newTemplateDesc, setNewTemplateDesc] = useState('')
  const [showNewTemplate, setShowNewTemplate] = useState(false)

  const handleCreateTemplate = () => {
    if (newTemplateName.trim()) {
      createTemplate(newTemplateName, newTemplateDesc)
      setNewTemplateName('')
      setNewTemplateDesc('')
      setShowNewTemplate(false)
    }
  }

  const totalWeight = (criteria: EvaluationCriteria[]) => {
    return criteria.reduce((sum, c) => sum + c.weight, 0)
  }

  const validateWeight = (criteria: EvaluationCriteria[]) => {
    return Math.abs(totalWeight(criteria) - 100) < 0.01
  }

  return (
    <div className="min-h-screen relative">
      {/* Subtle background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-400/8 dark:bg-brand-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/3 left-0 w-96 h-96 bg-purple-400/8 dark:bg-purple-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Policy Templates
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Create and manage evaluation criteria for LLM-based quality assurance
          </p>
        </div>
        <button
          onClick={() => setShowNewTemplate(true)}
          className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 flex items-center space-x-2"
        >
          <FaPlus className="w-4 h-4" />
          <span>New Template</span>
        </button>
      </div>

      {/* New Template Form */}
      {showNewTemplate && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Create New Template
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Template Name
              </label>
              <input
                type="text"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder="e.g., Customer Service QA"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={newTemplateDesc}
                onChange={(e) => setNewTemplateDesc(e.target.value)}
                placeholder="Describe what this template evaluates..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleCreateTemplate}
                className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowNewTemplate(false)
                  setNewTemplateName('')
                  setNewTemplateDesc('')
                }}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Templates List */}
      <div className="space-y-6">
        {templates.map((template) => {
          const isActive = activeTemplate?.id === template.id
          const weightsValid = validateWeight(template.criteria)
          const isEditing = editingTemplate === template.id

          return (
            <div
              key={template.id}
              className={`bg-white dark:bg-gray-800 rounded-lg border-2 ${
                isActive
                  ? 'border-brand-500 dark:border-brand-500'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              {/* Template Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {isEditing ? (
                      <div className="space-y-4">
                        <input
                          type="text"
                          value={template.name}
                          onChange={(e) =>
                            updateTemplate(template.id, { name: e.target.value })
                          }
                          className="text-xl font-semibold px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full"
                        />
                        <textarea
                          value={template.description}
                          onChange={(e) =>
                            updateTemplate(template.id, { description: e.target.value })
                          }
                          rows={2}
                          className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full"
                        />
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center space-x-3 mb-2">
                          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                            {template.name}
                          </h2>
                          {isActive && (
                            <span className="px-2 py-1 bg-brand-500 text-white text-xs rounded">
                              Active
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
                          onClick={() => setActiveTemplate(template.id)}
                          className={`px-3 py-1.5 rounded-lg text-sm ${
                            isActive
                              ? 'bg-brand-500 text-white'
                              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                          }`}
                        >
                          {isActive ? 'Active' : 'Set Active'}
                        </button>
                        <button
                          onClick={() => setEditingTemplate(template.id)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                        >
                          <FaEdit className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {isEditing && (
                      <button
                        onClick={() => setEditingTemplate(null)}
                        className="p-2 text-green-600 dark:text-green-400"
                      >
                        <FaSave className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (confirm('Delete this template?')) {
                          deleteTemplate(template.id)
                        }
                      }}
                      className="p-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    >
                      <FaTrash className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Criteria List */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Evaluation Criteria
                  </h3>
                  <button
                    onClick={() => {
                      addCriteria(template.id, {
                        categoryName: 'New Category',
                        weight: 0,
                        passingScore: 70,
                        evaluationPrompt: 'Evaluate this category...',
                      })
                    }}
                    className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-1 text-sm"
                  >
                    <FaPlus className="w-4 h-4" />
                    <span>Add Criteria</span>
                  </button>
                </div>

                {/* Weight Validation */}
                {!weightsValid && template.criteria.length > 0 && (
                  <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-center space-x-2">
                    <FaExclamationCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                    <span className="text-sm text-yellow-800 dark:text-yellow-200">
                      Total weight must equal 100%. Current: {totalWeight(template.criteria).toFixed(1)}%
                    </span>
                  </div>
                )}

                {template.criteria.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No criteria added yet. Click "Add Criteria" to get started.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {template.criteria.map((criteria) => {
                      const isEditingCriteria = editingCriteria === criteria.id

                      return (
                        <div
                          key={criteria.id}
                          className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                        >
                          {isEditingCriteria ? (
                            <CriteriaEditor
                              criteria={criteria}
                              onSave={(updates) => {
                                updateCriteria(template.id, criteria.id, updates)
                                setEditingCriteria(null)
                              }}
                              onCancel={() => setEditingCriteria(null)}
                            />
                          ) : (
                            <div>
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-3 mb-2">
                                    <h4 className="font-semibold text-gray-900 dark:text-white">
                                      {criteria.categoryName}
                                    </h4>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">
                                      Weight: {criteria.weight}% | Passing: {criteria.passingScore}%
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {criteria.evaluationPrompt}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-2 ml-4">
                                  <button
                                    onClick={() => setEditingCriteria(criteria.id)}
                                    className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                                  >
                                    <FaEdit className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => {
                                      if (confirm('Delete this criteria?')) {
                                        deleteCriteria(template.id, criteria.id)
                                      }
                                    }}
                                    className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
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
  const [categoryName, setCategoryName] = useState(criteria.categoryName)
  const [weight, setWeight] = useState(criteria.weight.toString())
  const [passingScore, setPassingScore] = useState(criteria.passingScore.toString())
  const [evaluationPrompt, setEvaluationPrompt] = useState(criteria.evaluationPrompt)

  const handleSave = () => {
    onSave({
      categoryName,
      weight: parseFloat(weight) || 0,
      passingScore: parseInt(passingScore) || 0,
      evaluationPrompt,
    })
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
