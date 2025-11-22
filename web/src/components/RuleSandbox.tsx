/**
 * Rule Sandbox Component
 * Phase 5: Structured Rule Editor UI & Admin Tools
 * 
 * Preview panel for testing rules on sample transcripts.
 * Shows rule-by-rule pass/fail + evidence, category-level penalties, warning flags.
 */

import { useState } from 'react'
import { FaCheckCircle, FaTimesCircle, FaExclamationTriangle } from 'react-icons/fa'
import { AlertModal } from '@/components/modals'

interface SandboxResult {
  rule_results: any
  expected_rubric_impacts: { [category: string]: string }
  critical_failures?: any[]
  warnings?: string[]
}

interface RuleSandboxProps {
  templateId: string
  onClose: () => void
}

export function RuleSandbox({ templateId, onClose }: RuleSandboxProps) {
  const [transcriptText, setTranscriptText] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SandboxResult | null>(null)
  const [alertModal, setAlertModal] = useState<{ isOpen: boolean; title: string; message: string; type: 'error' } | null>(null)

  const handleTest = async () => {
    if (!transcriptText.trim()) {
      setAlertModal({
        isOpen: true,
        title: 'Validation Error',
        message: 'Please enter transcript text',
        type: 'error',
      })
      return
    }

    // Parse transcript into segments (simplified)
    const segments = transcriptText.split('\n').map((line, idx) => {
      const parts = line.split(':')
      return {
        speaker: parts[0]?.trim().toLowerCase() || 'agent',
        text: parts.slice(1).join(':').trim(),
        start: idx * 5,
        end: (idx + 1) * 5
      }
    })

    try {
      setLoading(true)
      const response = await fetch(`/api/policy-templates/${templateId}/rules/sandbox`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript_segments: segments,
          sentiment_analysis: null
        })
      })
      const data = await response.json()
      setResults(data)
    } catch (err: any) {
      setAlertModal({
        isOpen: true,
        title: 'Error',
        message: `Failed to test rules: ${err.message}`,
        type: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Rule Sandbox Preview</h2>

        <div className="mb-4">
          <label className="block mb-2 font-medium">Sample Transcript</label>
          <textarea
            value={transcriptText}
            onChange={(e) => setTranscriptText(e.target.value)}
            className="w-full border rounded p-2"
            rows={10}
            placeholder="agent: Hello, how can I help you?&#10;caller: I have a problem..."
          />
        </div>

        <button
          onClick={handleTest}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mb-4"
        >
          {loading ? 'Testing...' : 'Test Rules'}
        </button>

        {results && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold mb-4">Results</h3>

            {/* Expected Rubric Impacts */}
            <div className="mb-6">
              <h4 className="font-medium mb-2">Expected Rubric Impacts</h4>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(results.expected_rubric_impacts || {}).map(([category, level]) => (
                  <div key={category} className="border p-2 rounded">
                    <div className="font-medium">{category}</div>
                    <div className="text-sm text-gray-600">{level}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Critical Failures */}
            {results.critical_failures && results.critical_failures.length > 0 && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded p-4">
                <h4 className="font-medium text-red-800 mb-2 flex items-center gap-2">
                  <FaExclamationTriangle /> Critical Failures
                </h4>
                {results.critical_failures.map((failure: any, idx: number) => (
                  <div key={idx} className="text-sm text-red-700">
                    {failure.category}.{failure.rule_id}: {failure.severity}
                  </div>
                ))}
              </div>
            )}

            {/* Rule Results */}
            <div>
              <h4 className="font-medium mb-2">Rule-by-Rule Results</h4>
              {Object.entries(results.rule_results || {}).map(([category, rules]: [string, any]) => {
                if (category === 'summary') return null
                return (
                  <div key={category} className="mb-4 border rounded p-4">
                    <h5 className="font-medium mb-2">{category}</h5>
                    {Object.entries(rules).map(([ruleId, result]: [string, any]) => (
                      <div
                        key={ruleId}
                        className={`p-2 mb-2 rounded flex items-center gap-2 ${
                          result.passed ? 'bg-green-50' : 'bg-red-50'
                        }`}
                      >
                        {result.passed ? (
                          <FaCheckCircle className="text-green-600" />
                        ) : (
                          <FaTimesCircle className="text-red-600" />
                        )}
                        <div className="flex-1">
                          <div className="font-medium">{ruleId}</div>
                          {result.evidence && result.evidence.length > 0 && (
                            <div className="text-sm text-gray-600">
                              Evidence: {JSON.stringify(result.evidence)}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Close
        </button>
      </div>

      {/* Alert Modal */}
      {alertModal && (
        <AlertModal
          isOpen={alertModal.isOpen}
          onClose={() => setAlertModal(null)}
          title={alertModal.title}
          message={alertModal.message}
          type={alertModal.type}
        />
      )}
    </div>
  )
}

