import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { FaExclamationCircle } from 'react-icons/fa'

interface PendingReview {
  evaluation_id: string
  recording_id: string
  recording_title: string
  ai_overall_score: number
  ai_stage_scores: Array<{
    stage_id?: string
    stage_name?: string
    name?: string
    score: number
    passed?: boolean
    feedback?: string
  }>
  ai_violations: Array<any>
  rule_engine_results: Record<string, any>
  confidence_score: number
  transcript_preview: string
  created_at: string
}

export function HumanReview() {
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([])
  const [currentReview, setCurrentReview] = useState<PendingReview | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [humanStageScores, setHumanStageScores] = useState<Array<{
    stage_id?: string
    stage_name?: string
    name?: string
    score: number
    feedback?: string
  }>>([])
  const [overallScore, setOverallScore] = useState<number>(0)
  const [showScorePrompt, setShowScorePrompt] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    loadPendingReviews()
    
    // Check for dark mode
    const checkDarkMode = () => {
      setIsDarkMode(document.documentElement.classList.contains('dark'))
    }
    checkDarkMode()
    
    // Watch for theme changes
    const observer = new MutationObserver(checkDarkMode)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    })
    
    return () => observer.disconnect()
  }, [])

  // Calculate overall score automatically based on stage scores
  useEffect(() => {
    if (humanStageScores.length === 0) {
      setOverallScore(0)
      return
    }

    const scores = humanStageScores.map(s => s.score).filter(s => s > 0)
    if (scores.length > 0) {
      const avg = scores.reduce((a, b) => a + b, 0) / scores.length
      setOverallScore(Math.round(avg))
    } else {
      setOverallScore(0)
    }
  }, [humanStageScores])

  const loadPendingReviews = async () => {
    try {
      setLoading(true)
      const reviews = await api.getPendingReviews({ limit: 10 })
      setPendingReviews(reviews)
      if (reviews.length > 0) {
        setCurrentReview(reviews[0])
        // Initialize human stage scores with AI stage scores as starting point
        setHumanStageScores(reviews[0].ai_stage_scores.map(stage => ({
          stage_id: stage.stage_id,
          stage_name: stage.stage_name || stage.name,
          name: stage.name,
          score: stage.score || 0,
          feedback: stage.feedback || ''
        })))
        setOverallScore(reviews[0].ai_overall_score)
      }
    } catch (error) {
      console.error('Failed to load pending reviews:', error)
      setMessage('Failed to load pending reviews')
    } finally {
      setLoading(false)
    }
  }

  const formatTranscript = () => {
    return currentReview?.transcript_preview || ''
  }

  const submitReview = async () => {
    if (!currentReview) return

    try {
      setSubmitting(true)
      await api.submitHumanReview(currentReview.evaluation_id, {
        human_overall_score: overallScore,
        human_stage_scores: humanStageScores,
        reviewer_notes: message || undefined
      })

      setMessage('Review submitted successfully!')

      // Remove current review and load next one
      const remainingReviews = pendingReviews.filter(r => r.evaluation_id !== currentReview.evaluation_id)
      setPendingReviews(remainingReviews)

      if (remainingReviews.length > 0) {
        setCurrentReview(remainingReviews[0])
        setHumanStageScores(remainingReviews[0].ai_stage_scores.map(stage => ({
          stage_id: stage.stage_id,
          stage_name: stage.stage_name || stage.name,
          name: stage.name,
          score: stage.score || 0,
          feedback: stage.feedback || ''
        })))
        setOverallScore(remainingReviews[0].ai_overall_score)
      } else {
        setCurrentReview(null)
        setHumanStageScores([])
        setOverallScore(0)
      }

      setTimeout(() => setMessage(''), 3000)
    } catch (error) {
      console.error('Failed to submit review:', error)
      setMessage('Failed to submit review')
    } finally {
      setSubmitting(false)
    }
  }

  const skipReview = async () => {
    const remainingReviews = pendingReviews.filter(r => r.evaluation_id !== currentReview?.evaluation_id)
    setPendingReviews(remainingReviews)

    if (remainingReviews.length > 0) {
      setCurrentReview(remainingReviews[0])
      setHumanStageScores(remainingReviews[0].ai_stage_scores.map(stage => ({
        stage_id: stage.stage_id,
        stage_name: stage.stage_name || stage.name,
        name: stage.name,
        score: stage.score || 0,
        feedback: stage.feedback || ''
      })))
      setOverallScore(remainingReviews[0].ai_overall_score)
    } else {
        setCurrentReview(null)
        setHumanStageScores([])
        setOverallScore(0)
      setTemplateDetails(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-400">Loading pending reviews...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen relative">
      {/* Background effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-yellow-400/8 dark:bg-yellow-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/3 right-0 w-96 h-96 bg-green-400/8 dark:bg-green-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-orange-400/8 dark:bg-orange-500/3 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Human Review Queue</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Review AI evaluations that need human validation. Your feedback helps improve the system.
          </p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.includes('success') ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'}`}>
            {message}
          </div>
        )}

        {!currentReview ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 border border-gray-200 dark:border-gray-700 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">All Caught Up!</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No pending reviews at the moment. The AI is performing well or there are no evaluations requiring human review.
            </p>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p>To test the human review system:</p>
              <ol className="list-decimal list-inside mt-2 text-left inline-block">
                <li>Upload and process a recording</li>
                <li>If AI confidence is low (&lt;80%), it will appear here</li>
                <li>Or manually create a test review from the results page</li>
              </ol>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* Transcript Section */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Call Transcript</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Evaluation ID: {currentReview.evaluation_id.slice(0, 8)}... | Created: {new Date(currentReview.created_at).toLocaleString()}
                </p>
              </div>
              <div className="p-6 overflow-y-auto" style={{ maxHeight: '600px' }}>
                <div className="prose dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-mono">
                    {currentReview.transcript_preview}
                  </pre>
                </div>
              </div>
            </div>

            {/* Review Form */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Your Evaluation</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Compare your scores with the AI's evaluation below
                </p>
              </div>

              <div className="p-6 space-y-6">
                {/* AI Evaluation Summary */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
                    <FaExclamationCircle className="w-5 h-5 mr-2" />
                    AI's Evaluation Summary
                  </h3>
                  <div className="mb-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-blue-800 dark:text-blue-200">Overall Score:</span>
                      <span className="text-lg font-bold text-blue-900 dark:text-blue-100">
                        {currentReview.ai_overall_score}/100
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Stage Scores:</p>
                    {currentReview.ai_stage_scores.map((stage: any, idx: number) => (
                      <div key={stage.stage_id || idx} className="flex items-center justify-between text-sm">
                        <span className="text-blue-700 dark:text-blue-300">{stage.stage_name || stage.name || `Stage ${idx + 1}`}:</span>
                        <span className="font-semibold text-blue-900 dark:text-blue-100">
                          {stage.score || 0}/100
                        </span>
                      </div>
                    ))}
                  </div>
                  {currentReview.ai_violations && currentReview.ai_violations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
                      <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
                        Detected Violations: {currentReview.ai_violations.length}
                      </p>
                    </div>
                  )}
                </div>
                {/* Stage Scores */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Your Stage Scores
                    <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                      (Compare with AI scores above)
                    </span>
                  </h3>
                  <div className="space-y-4">
                    {currentReview.ai_stage_scores.map((aiStage: any, idx: number) => {
                      const humanStage = humanStageScores.find(h => 
                        (h.stage_id && aiStage.stage_id && h.stage_id === aiStage.stage_id) ||
                        (h.stage_name && aiStage.stage_name && h.stage_name === aiStage.stage_name) ||
                        (h.name && aiStage.name && h.name === aiStage.name)
                      ) || humanStageScores[idx] || { score: 0, feedback: '' }
                      
                      return (
                        <div key={aiStage.stage_id || idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                          <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                            {aiStage.stage_name || aiStage.name || `Stage ${idx + 1}`}
                          </h4>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">AI Score</div>
                              <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                                {aiStage.score || 0}<span className="text-sm text-blue-600 dark:text-blue-400">/100</span>
                              </div>
                            </div>
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">Your Score</div>
                              <div className="flex items-center space-x-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={humanStage.score || 0}
                                  onChange={(e) => {
                                    const newScores = [...humanStageScores]
                                    const existingIndex = newScores.findIndex(h => 
                                      (h.stage_id && aiStage.stage_id && h.stage_id === aiStage.stage_id) ||
                                      (h.stage_name && aiStage.stage_name && h.stage_name === aiStage.stage_name)
                                    )
                                    if (existingIndex >= 0) {
                                      newScores[existingIndex] = {
                                        ...newScores[existingIndex],
                                        score: parseInt(e.target.value) || 0
                                      }
                                    } else {
                                      newScores[idx] = {
                                        stage_id: aiStage.stage_id,
                                        stage_name: aiStage.stage_name || aiStage.name,
                                        name: aiStage.name,
                                        score: parseInt(e.target.value) || 0,
                                        feedback: humanStage.feedback || ''
                                      }
                                    }
                                    setHumanStageScores(newScores)
                                  }}
                                  className="w-16 px-2 py-1 text-2xl font-bold border-0 bg-transparent focus:ring-2 focus:ring-green-500 rounded text-green-900 dark:text-green-100"
                                />
                                <span className="text-sm text-green-600 dark:text-green-400">/100</span>
                              </div>
                            </div>
                          </div>
                          {aiStage.feedback && (
                            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                <strong>AI Feedback:</strong> {aiStage.feedback}
                              </p>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Overall Score */}
                <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Overall Score (Auto-calculated)
                    <span className="text-xs font-normal text-gray-500 dark:text-gray-400 ml-2">
                      Based on average of stage scores
                    </span>
                  </label>
                  <div className="flex items-center space-x-3">
                    <div className="flex-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-3">
                      <span className="text-2xl font-bold text-gray-900 dark:text-white">
                        {overallScore}
                      </span>
                      <span className="text-lg text-gray-600 dark:text-gray-400 ml-1">/100</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setShowScorePrompt(true)
                      }}
                      className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      Override
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Calculated from: {humanStageScores.filter(s => s.score > 0).map(s => `${s.stage_name || s.name || 'Stage'} (${s.score})`).join(', ') || 'No scores entered yet'}
                  </p>
                </div>


                {/* Violations */}
                {currentReview.ai_violations && currentReview.ai_violations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">AI-Detected Violations</h3>
                    <div className="space-y-2">
                      {currentReview.ai_violations.map((violation: any, index: number) => (
                        <div key={index} className="p-3 bg-red-50 dark:bg-red-900/20 rounded-md">
                          <p className="text-sm font-medium text-red-800 dark:text-red-200">
                            {violation.type} ({violation.severity})
                          </p>
                          <p className="text-sm text-red-700 dark:text-red-300">
                            {violation.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-4 pt-6">
                  <button
                    onClick={submitReview}
                    disabled={submitting}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                  >
                    {submitting ? 'Submitting...' : 'Submit Review'}
                  </button>
                  <button
                    onClick={skipReview}
                    className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Skip
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pending Reviews Counter */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Queue Status</h3>
          <p className="text-gray-600 dark:text-gray-400">
            {pendingReviews.length} pending review{pendingReviews.length !== 1 ? 's' : ''} remaining
          </p>
        </div>
      </div>

      {/* Score Prompt Modal */}
      {showScorePrompt && (
        <PromptModal
          isOpen={showScorePrompt}
          onClose={() => setShowScorePrompt(false)}
          onConfirm={(value) => {
            const score = parseInt(value)
            if (!isNaN(score) && score >= 0 && score <= 100) {
              setOverallScore(score)
            }
            setShowScorePrompt(false)
          }}
          title="Override Score"
          message="Enter a new score (0-100):"
          defaultValue={overallScore.toString()}
          inputType="number"
          confirmText="Set Score"
          cancelText="Cancel"
          required
          validator={(value) => {
            const score = parseInt(value)
            if (isNaN(score)) return 'Please enter a valid number'
            if (score < 0 || score > 100) return 'Score must be between 0 and 100'
            return true
          }}
        />
      )}
    </div>
  )
}
