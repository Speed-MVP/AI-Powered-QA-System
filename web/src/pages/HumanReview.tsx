import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { FaPlay, FaPause, FaVolumeUp, FaExclamationCircle, FaStar } from 'react-icons/fa'

interface PendingReview {
  review_id: string
  evaluation_id: string
  transcript_text: string
  diarized_segments: Array<{
    speaker: string
    text: string
    start: number
    end: number
  }>
  audio_url: string | null
  ai_overall_score: number
  ai_category_scores: Record<string, any>
  ai_violations: any[]
  created_at: string
}

export function HumanReview() {
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([])
  const [currentReview, setCurrentReview] = useState<PendingReview | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [humanScores, setHumanScores] = useState<Record<string, number>>({})
  const [overallScore, setOverallScore] = useState<number>(0)
  const [aiAccuracy, setAiAccuracy] = useState<number>(3)
  const [message, setMessage] = useState<string>('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioTime, setAudioTime] = useState(0)
  const [audioDuration, setAudioDuration] = useState(0)
  const [templateDetails, setTemplateDetails] = useState<any>(null)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const audioRef = useRef<HTMLAudioElement>(null)

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

  // Calculate overall score automatically based on category scores
  useEffect(() => {
    if (!templateDetails || !templateDetails.criteria) {
      // Fallback: simple average if no template
      const scores = Object.values(humanScores).filter(s => s > 0)
      if (scores.length > 0) {
        const avg = scores.reduce((a, b) => a + b, 0) / scores.length
        setOverallScore(Math.round(avg))
      } else {
        setOverallScore(0)
      }
      return
    }

    // Calculate weighted average based on criteria weights
    let totalWeightedScore = 0
    let totalWeight = 0

    templateDetails.criteria.forEach((criterion: any) => {
      const score = humanScores[criterion.category_name] || 0
      const weight = criterion.weight || 0
      
      if (score > 0 && weight > 0) {
        totalWeightedScore += score * (weight / 100)
        totalWeight += weight / 100
      }
    })

    if (totalWeight > 0) {
      const calculatedScore = Math.round(totalWeightedScore / totalWeight)
      setOverallScore(calculatedScore)
    } else {
      // If no scores entered yet, show 0
      setOverallScore(0)
    }
  }, [humanScores, templateDetails])

  const loadPendingReviews = async () => {
    try {
      setLoading(true)
      const reviews = await api.getPendingReviews({ limit: 10 })
      setPendingReviews(reviews)
      if (reviews.length > 0) {
        setCurrentReview(reviews[0])
        // Initialize human scores with AI scores as starting point
        const initialScores: Record<string, number> = {}
        Object.entries(reviews[0].ai_category_scores).forEach(([category, data]: [string, any]) => {
          initialScores[category] = data.score || 0
        })
        setHumanScores(initialScores)
        setOverallScore(reviews[0].ai_overall_score)

        // Fetch template details for detailed criteria display
        try {
          const evaluationDetails = await api.getEvaluationWithTemplate(reviews[0].evaluation_id)
          setTemplateDetails(evaluationDetails.template)
        } catch (error) {
          console.error('Failed to load template details:', error)
        }
      }
    } catch (error) {
      console.error('Failed to load pending reviews:', error)
      setMessage('Failed to load pending reviews')
    } finally {
      setLoading(false)
    }
  }

  const toggleAudio = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
  }

  const handleAudioTimeUpdate = () => {
    if (audioRef.current) {
      setAudioTime(audioRef.current.currentTime)
    }
  }

  const handleAudioLoadedMetadata = () => {
    if (audioRef.current) {
      setAudioDuration(audioRef.current.duration)
    }
  }

  const handleAudioEnded = () => {
    setIsPlaying(false)
    setAudioTime(0)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return
    const newTime = parseFloat(e.target.value)
    audioRef.current.currentTime = newTime
    setAudioTime(newTime)
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const formatTranscript = (segments: Array<{speaker: string, text: string, start: number, end: number}>) => {
    if (!segments || segments.length === 0) {
      return currentReview?.transcript_text || ''
    }

    return segments.map((segment, index) => {
      const speaker = segment.speaker.toLowerCase().includes('agent') ? 'Agent' : 'Caller'
      return `${speaker}: ${segment.text}`
    }).join('\n\n')
  }

  const submitReview = async () => {
    if (!currentReview) return

    try {
      setSubmitting(true)
      await api.submitHumanReview(currentReview.review_id, {
        human_overall_score: overallScore,
        human_category_scores: humanScores,
        ai_score_accuracy: aiAccuracy
      })

      setMessage('Review submitted successfully!')

      // Remove current review and load next one
      const remainingReviews = pendingReviews.filter(r => r.review_id !== currentReview.review_id)
      setPendingReviews(remainingReviews)

      if (remainingReviews.length > 0) {
        setCurrentReview(remainingReviews[0])
        const initialScores: Record<string, number> = {}
        Object.entries(remainingReviews[0].ai_category_scores).forEach(([category, data]: [string, any]) => {
          initialScores[category] = data.score || 0
        })
        setHumanScores(initialScores)
        
        // Fetch template details for the new review
        try {
          const evaluationDetails = await api.getEvaluationWithTemplate(remainingReviews[0].evaluation_id)
          setTemplateDetails(evaluationDetails.template)
        } catch (error) {
          console.error('Failed to load template details:', error)
          setTemplateDetails(null)
        }
        
        // Overall score will be auto-calculated by useEffect
      } else {
        setCurrentReview(null)
        setHumanScores({})
        setOverallScore(0)
        setTemplateDetails(null)
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
    const remainingReviews = pendingReviews.filter(r => r.review_id !== currentReview?.review_id)
    setPendingReviews(remainingReviews)

    if (remainingReviews.length > 0) {
      setCurrentReview(remainingReviews[0])
      const initialScores: Record<string, number> = {}
      Object.entries(remainingReviews[0].ai_category_scores).forEach(([category, data]: [string, any]) => {
        initialScores[category] = data.score || 0
      })
      setHumanScores(initialScores)
      
      // Fetch template details for the new review
      try {
        const evaluationDetails = await api.getEvaluationWithTemplate(remainingReviews[0].evaluation_id)
        setTemplateDetails(evaluationDetails.template)
      } catch (error) {
        console.error('Failed to load template details:', error)
        setTemplateDetails(null)
      }
      
      // Overall score will be auto-calculated by useEffect
    } else {
      setCurrentReview(null)
      setHumanScores({})
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
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Call Transcript & Audio</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Review ID: {currentReview.review_id} | Created: {new Date(currentReview.created_at).toLocaleString()}
                    </p>
                  </div>
                  {currentReview.audio_url && (
                    <div className="mt-4 space-y-3">
                      {/* Audio Progress Slider */}
                      <div className="flex items-center space-x-3">
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-12 text-right">
                          {formatTime(audioTime)}
                        </span>
                        <input
                          type="range"
                          min="0"
                          max={audioDuration || 0}
                          value={audioTime}
                          onChange={handleSeek}
                          step="0.1"
                          className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                          style={{
                            background: audioDuration > 0 
                              ? `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(audioTime / audioDuration) * 100}%, ${isDarkMode ? '#374151' : '#e5e7eb'} ${(audioTime / audioDuration) * 100}%, ${isDarkMode ? '#374151' : '#e5e7eb'} 100%)`
                              : undefined
                          }}
                        />
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-12">
                          {formatTime(audioDuration)}
                        </span>
                      </div>
                      
                      {/* Play/Pause Button */}
                      <div className="flex items-center justify-center">
                        <button
                          onClick={toggleAudio}
                          className="flex items-center justify-center w-12 h-12 bg-blue-500 hover:bg-blue-600 text-white rounded-full transition-colors shadow-lg hover:shadow-xl"
                        >
                          {isPlaying ? <FaPause className="w-5 h-5" /> : <FaPlay className="w-5 h-5 ml-0.5" />}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                {currentReview.audio_url && (
                  <audio
                    ref={audioRef}
                    src={currentReview.audio_url}
                    onTimeUpdate={handleAudioTimeUpdate}
                    onLoadedMetadata={handleAudioLoadedMetadata}
                    onEnded={handleAudioEnded}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    className="hidden"
                  />
                )}
              </div>
              <div className="p-6 overflow-y-auto" style={{ maxHeight: '600px' }}>
                <div className="space-y-4">
                  {currentReview.diarized_segments && currentReview.diarized_segments.length > 0 ? (
                    currentReview.diarized_segments.map((segment, index) => {
                      const speaker = segment.speaker.toLowerCase().includes('agent') ? 'Agent' : 'Caller'
                      const isAgent = speaker === 'Agent'
                      return (
                        <div key={index} className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            isAgent
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                          }`}>
                            <div className="text-xs font-medium mb-1 opacity-75">
                              {speaker} • {formatTime(segment.start)}
                            </div>
                            <div className="text-sm">{segment.text}</div>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <div className="prose dark:prose-invert max-w-none">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-mono">
                        {currentReview.transcript_text}
                      </pre>
                    </div>
                  )}
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
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Category Scores:</p>
                    {Object.entries(currentReview.ai_category_scores).map(([category, data]: [string, any]) => (
                      <div key={category} className="flex items-center justify-between text-sm">
                        <span className="text-blue-700 dark:text-blue-300">{category}:</span>
                        <span className="font-semibold text-blue-900 dark:text-blue-100">
                          {data.score || 0}/100
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
                {/* Category Scores with Detailed Criteria */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Your Category Scores
                    <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                      (Compare with AI scores above)
                    </span>
                  </h3>
                  {!templateDetails ? (
                    <div className="space-y-4">
                      {Object.entries(currentReview.ai_category_scores).map(([category, data]: [string, any]) => (
                        <div key={category} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                          <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                            {category}
                          </h4>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">AI Score</div>
                              <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                                {data.score || 0}<span className="text-sm text-blue-600 dark:text-blue-400">/100</span>
                              </div>
                            </div>
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">Your Score</div>
                              <div className="flex items-center space-x-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={humanScores[category] || 0}
                                  onChange={(e) => setHumanScores(prev => ({
                                    ...prev,
                                    [category]: parseInt(e.target.value) || 0
                                  }))}
                                  className="w-16 px-2 py-1 text-2xl font-bold border-0 bg-transparent focus:ring-2 focus:ring-green-500 rounded text-green-900 dark:text-green-100"
                                />
                                <span className="text-sm text-green-600 dark:text-green-400">/100</span>
                              </div>
                            </div>
                          </div>
                          {data.feedback && (
                            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                <strong>AI Feedback:</strong> {data.feedback}
                              </p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {templateDetails.criteria?.map((criterion: any) => {
                      const aiScoreData = currentReview.ai_category_scores[criterion.category_name]
                      const humanScore = humanScores[criterion.category_name] || 0

                      return (
                        <div key={criterion.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                          <div className="mb-3">
                            <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">
                              {criterion.category_name}
                            </h4>
                            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                              <span>Weight: {criterion.weight}%</span>
                              <span>Passing: {criterion.passing_score}/100</span>
                            </div>
                          </div>

                          {/* Score Comparison */}
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            {/* AI Score */}
                            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">
                                AI Score
                              </div>
                              <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                                {aiScoreData?.score || 0}
                                <span className="text-sm text-blue-600 dark:text-blue-400">/100</span>
                              </div>
                            </div>

                            {/* Human Score */}
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                              <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">
                                Your Score
                              </div>
                              <div className="flex items-center space-x-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={humanScore}
                                  onChange={(e) => setHumanScores(prev => ({
                                    ...prev,
                                    [criterion.category_name]: parseInt(e.target.value) || 0
                                  }))}
                                  className="w-16 px-2 py-1 text-2xl font-bold border-0 bg-transparent focus:ring-2 focus:ring-green-500 rounded text-green-900 dark:text-green-100"
                                />
                                <span className="text-sm text-green-600 dark:text-green-400">/100</span>
                              </div>
                            </div>
                          </div>

                          {/* Score Difference Indicator */}
                          {humanScore !== (aiScoreData?.score || 0) && (
                            <div className={`mb-3 p-2 rounded-md text-xs ${
                              Math.abs(humanScore - (aiScoreData?.score || 0)) > 10
                                ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200'
                                : 'bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                            }`}>
                              <strong>Difference:</strong> {humanScore > (aiScoreData?.score || 0) ? '+' : ''}
                              {humanScore - (aiScoreData?.score || 0)} points from AI score
                            </div>
                          )}

                          {/* AI Feedback */}
                          {aiScoreData?.feedback && (
                            <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                <strong>AI Feedback:</strong> {aiScoreData.feedback}
                              </p>
                            </div>
                          )}

                          {/* Rubric Levels */}
                          <div className="space-y-2">
                            <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">Scoring Guide:</h5>
                            {criterion.rubric_levels?.map((level: any) => (
                              <div key={level.id} className={`p-3 rounded-md border-l-4 ${
                                humanScore >= level.min_score && humanScore <= level.max_score
                                  ? 'border-l-green-500 bg-green-50 dark:bg-green-900/20'
                                  : 'border-l-gray-300 dark:border-l-gray-600'
                              }`}>
                                <div className="flex items-center justify-between">
                                  <h6 className="text-sm font-medium text-gray-900 dark:text-white">
                                    {level.level_name} ({level.min_score}-{level.max_score})
                                  </h6>
                                  {humanScore >= level.min_score && humanScore <= level.max_score && (
                                    <span className="text-green-600 dark:text-green-400 text-sm font-medium">Current Score</span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {level.description}
                                </p>
                                {level.examples && (
                                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1 italic">
                                    Examples: {level.examples}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    })}
                    </div>
                  )}
                </div>

                {/* Overall Score */}
                <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Overall Score (Auto-calculated)
                    <span className="text-xs font-normal text-gray-500 dark:text-gray-400 ml-2">
                      Based on weighted category scores
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
                        const newScore = prompt('Override auto-calculated score:', overallScore.toString())
                        if (newScore !== null) {
                          const score = parseInt(newScore)
                          if (!isNaN(score) && score >= 0 && score <= 100) {
                            setOverallScore(score)
                          }
                        }
                      }}
                      className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      Override
                    </button>
                  </div>
                  {templateDetails && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Calculated from: {templateDetails.criteria?.filter((c: any) => (humanScores[c.category_name] || 0) > 0).map((c: any) => `${c.category_name} (${c.weight}%)`).join(', ') || 'No scores entered yet'}
                    </p>
                  )}
                </div>

                {/* AI Accuracy Rating */}
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <div className="mb-3">
                    <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                      Rate the AI's Evaluation Accuracy
                    </label>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                      Based on the AI's evaluation shown above (overall score: {currentReview.ai_overall_score}/100, 
                      category scores, and detected violations), how accurate do you think the AI was?
                    </p>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      {[1, 2, 3, 4, 5].map(rating => (
                        <button
                          key={rating}
                          onClick={() => setAiAccuracy(rating)}
                          className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all ${
                            aiAccuracy === rating
                              ? 'bg-blue-500 border-blue-500 text-white scale-110'
                              : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-400 hover:scale-105'
                          }`}
                        >
                          {rating === aiAccuracy ? <FaStar className="w-4 h-4" /> : rating}
                        </button>
                      ))}
                    </div>
                    <div className="text-sm">
                      {aiAccuracy === 1 && <p className="text-red-600 dark:text-red-400">Poor: AI evaluation was completely inaccurate or missed major issues</p>}
                      {aiAccuracy === 2 && <p className="text-orange-600 dark:text-orange-400">Below Average: AI missed several important details or scored incorrectly</p>}
                      {aiAccuracy === 3 && <p className="text-yellow-600 dark:text-yellow-400">Acceptable: AI evaluation was reasonable but had some errors</p>}
                      {aiAccuracy === 4 && <p className="text-green-600 dark:text-green-400">Good: AI evaluation was mostly accurate with minor issues</p>}
                      {aiAccuracy === 5 && <p className="text-green-700 dark:text-green-500 font-medium">Excellent: AI evaluation was highly accurate and comprehensive</p>}
                    </div>
                  </div>
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
    </div>
  )
}
