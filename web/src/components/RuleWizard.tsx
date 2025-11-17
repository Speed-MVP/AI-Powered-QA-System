/**
 * Rule Add/Edit Wizard
 * Phase 5: Structured Rule Editor UI & Admin Tools
 * 
 * Multi-step wizard for adding/editing rules:
 * Step 1: Select rule type
 * Step 2: Fill required fields
 * Step 3: Rule-specific inputs
 * Step 4: Preview JSON + examples
 * Step 5: Save to draft
 */

import { useState } from 'react'
import { FaArrowLeft, FaArrowRight, FaCheck } from 'react-icons/fa'

interface RuleWizardProps {
  onSave: (rule: any) => void
  onCancel: () => void
  initialRule?: any
}

const RULE_TYPES = [
  { value: 'boolean', label: 'Boolean' },
  { value: 'numeric', label: 'Numeric' },
  { value: 'phrase', label: 'Phrase' },
  { value: 'list', label: 'List' },
  { value: 'conditional', label: 'Conditional' },
  { value: 'multi_step', label: 'Multi-Step' },
  { value: 'tone_based', label: 'Tone-Based' },
  { value: 'resolution', label: 'Resolution' }
]

const SEVERITIES = ['minor', 'moderate', 'major', 'critical']
const CATEGORIES = ['Professionalism', 'Empathy', 'Resolution']

export function RuleWizard({ onSave, onCancel, initialRule }: RuleWizardProps) {
  const [step, setStep] = useState(1)
  const [rule, setRule] = useState<any>(initialRule || {
    id: '',
    type: '',
    category: '',
    severity: 'moderate',
    enabled: true,
    description: '',
    critical: false
  })

  const updateRule = (updates: any) => {
    setRule({ ...rule, ...updates })
  }

  const handleNext = () => {
    if (step < 5) {
      setStep(step + 1)
    }
  }

  const handlePrev = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  const handleSave = () => {
    onSave(rule)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">
          {initialRule ? 'Edit Rule' : 'Add Rule'} - Step {step} of 5
        </h2>

        {/* Step 1: Select Rule Type */}
        {step === 1 && (
          <div>
            <label className="block mb-2 font-medium">Rule Type</label>
            <div className="grid grid-cols-2 gap-2">
              {RULE_TYPES.map(type => (
                <button
                  key={type.value}
                  onClick={() => updateRule({ type: type.value })}
                  className={`p-4 border rounded hover:bg-gray-50 ${
                    rule.type === type.value ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Required Fields */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="block mb-1 font-medium">Rule ID</label>
              <input
                type="text"
                value={rule.id}
                onChange={(e) => updateRule({ id: e.target.value })}
                className="w-full border rounded p-2"
                placeholder="snake_case_rule_id"
              />
            </div>
            <div>
              <label className="block mb-1 font-medium">Description</label>
              <textarea
                value={rule.description}
                onChange={(e) => updateRule({ description: e.target.value })}
                className="w-full border rounded p-2"
                rows={3}
              />
            </div>
            <div>
              <label className="block mb-1 font-medium">Category</label>
              <select
                value={rule.category}
                onChange={(e) => updateRule({ category: e.target.value })}
                className="w-full border rounded p-2"
              >
                <option value="">Select category</option>
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block mb-1 font-medium">Severity</label>
              <select
                value={rule.severity}
                onChange={(e) => updateRule({ severity: e.target.value })}
                className="w-full border rounded p-2"
              >
                {SEVERITIES.map(sev => (
                  <option key={sev} value={sev}>{sev}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={rule.enabled}
                onChange={(e) => updateRule({ enabled: e.target.checked })}
                id="enabled"
              />
              <label htmlFor="enabled">Enabled</label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={rule.critical}
                onChange={(e) => updateRule({ critical: e.target.checked })}
                id="critical"
              />
              <label htmlFor="critical">Critical Rule</label>
            </div>
          </div>
        )}

        {/* Step 3: Rule-Specific Inputs */}
        {step === 3 && (
          <div className="space-y-4">
            {rule.type === 'numeric' && (
              <>
                <div>
                  <label className="block mb-1 font-medium">Comparator</label>
                  <select
                    value={rule.comparator || ''}
                    onChange={(e) => updateRule({ comparator: e.target.value })}
                    className="w-full border rounded p-2"
                  >
                    <option value="le">Less than or equal (≤)</option>
                    <option value="lt">Less than (&lt;)</option>
                    <option value="ge">Greater than or equal (≥)</option>
                    <option value="gt">Greater than (&gt;)</option>
                    <option value="eq">Equal (==)</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-1 font-medium">Value</label>
                  <input
                    type="number"
                    value={rule.value || ''}
                    onChange={(e) => updateRule({ value: parseFloat(e.target.value) })}
                    className="w-full border rounded p-2"
                  />
                </div>
              </>
            )}
            {rule.type === 'phrase' && (
              <>
                <div>
                  <label className="block mb-1 font-medium">Phrases (one per line)</label>
                  <textarea
                    value={rule.phrases?.join('\n') || ''}
                    onChange={(e) => updateRule({ phrases: e.target.value.split('\n').filter(p => p.trim()) })}
                    className="w-full border rounded p-2"
                    rows={5}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={rule.required || false}
                    onChange={(e) => updateRule({ required: e.target.checked })}
                    id="required"
                  />
                  <label htmlFor="required">Required (unchecked = forbidden)</label>
                </div>
              </>
            )}
            {/* Add more rule type specific inputs as needed */}
          </div>
        )}

        {/* Step 4: Preview */}
        {step === 4 && (
          <div>
            <label className="block mb-2 font-medium">Rule Preview (JSON)</label>
            <pre className="bg-gray-100 p-4 rounded overflow-auto">
              {JSON.stringify(rule, null, 2)}
            </pre>
          </div>
        )}

        {/* Step 5: Save */}
        {step === 5 && (
          <div>
            <p className="mb-4">Ready to save this rule to draft?</p>
            <div className="bg-green-50 border border-green-200 rounded p-4">
              <p className="text-green-800">Rule will be saved as a draft. You can publish it later.</p>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            onClick={step === 1 ? onCancel : handlePrev}
            className="px-4 py-2 border rounded hover:bg-gray-50 flex items-center gap-2"
          >
            <FaArrowLeft /> {step === 1 ? 'Cancel' : 'Previous'}
          </button>
          {step < 5 ? (
            <button
              onClick={handleNext}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
            >
              Next <FaArrowRight />
            </button>
          ) : (
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2"
            >
              <FaCheck /> Save to Draft
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

