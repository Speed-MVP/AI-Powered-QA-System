import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaArrowLeft, FaChartBar, FaExclamationCircle, FaPlay, FaPause, FaSpinner, FaVolumeUp, FaChevronDown, FaChevronRight, FaFileCsv, FaFileAlt } from 'react-icons/fa'

type EvaluationResponse = Awaited<ReturnType<typeof api.getEvaluation>>
type TranscriptResponse = Awaited<ReturnType<typeof api.getTranscript>>
type RecordingResponse = Awaited<ReturnType<typeof api.getRecording>>
type TemplatesResponse = Awaited<ReturnType<typeof api.getTemplates>>

// Cache templates (they don't change often)
let templatesCache: TemplatesResponse | null = null
let templatesCacheTime: number = 0
const TEMPLATES_CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export function Results() {
  const { recordingId } = useParams<{ recordingId: string }>()
  const navigate = useNavigate()
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const isLoadingRef = useRef(false)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [recording, setRecording] = useState<RecordingResponse | null>(null)
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null)
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [policyTemplate, setPolicyTemplate] = useState<TemplatesResponse[number] | null>(null)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [creatingReview, setCreatingReview] = useState(false)

  useEffect(() => {
    if (!recordingId) {
      setError('Missing recording ID')
      setLoading(false)
      return
    }

    // Prevent concurrent fetches
    if (isLoadingRef.current) {
      return
    }

    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new AbortController for this request
    const abortController = new AbortController()
    abortControllerRef.current = abortController
    isLoadingRef.current = true

    const loadAll = async () => {
      try {
        setLoading(true)
        setError(null)

        const rec = await api.getRecording(recordingId)
        
        // Check if request was aborted
        if (abortController.signal.aborted) return
        
        setRecording(rec)

        if (rec.status !== 'completed') {
          setLoading(false)
          isLoadingRef.current = false
          return
        }

        // Fetch all data in parallel
        const [evalRes, transcriptRes, dl] = await Promise.all([
          api.getEvaluation(recordingId),
          api.getTranscript(recordingId).catch(() => null),
          api.getDownloadUrl(recordingId).catch(() => null),
        ])

        // Check if request was aborted
        if (abortController.signal.aborted) return

        setEvaluation(evalRes)
        if (transcriptRes) setTranscript(transcriptRes)
        if (dl?.download_url) setAudioUrl(dl.download_url)

        // Load policy template metadata via templates API (with caching)
        try {
          const now = Date.now()
          let templates: TemplatesResponse
          
          // Use cache if available and fresh
          if (templatesCache && (now - templatesCacheTime) < TEMPLATES_CACHE_TTL) {
            templates = templatesCache
          } else {
            templates = await api.getTemplates()
            templatesCache = templates
            templatesCacheTime = now
          }
          
          // Check if request was aborted
          if (abortController.signal.aborted) return
          
          const tpl = templates.find(t => t.id === evalRes.policy_template_id) || null
          setPolicyTemplate(tpl)
        } catch {
          // non-fatal
        }
      } catch (e: any) {
        // Don't set error if request was aborted
        if (!abortController.signal.aborted) {
          setError(e.message || 'Failed to load results')
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false)
          isLoadingRef.current = false
        }
      }
    }

    loadAll()

    // Cleanup: abort request if component unmounts or recordingId changes
    return () => {
      abortController.abort()
      isLoadingRef.current = false
    }
  }, [recordingId])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    const onEnded = () => setIsPlaying(false)
    const onPlay = () => setIsPlaying(true)
    const onPause = () => setIsPlaying(false)
    audio.addEventListener('ended', onEnded)
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    return () => {
      audio.removeEventListener('ended', onEnded)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
    }
  }, [audioUrl])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleRefresh = async () => {
    if (!recordingId || refreshing) return
    
    // Invalidate templates cache on refresh
    templatesCache = null
    templatesCacheTime = 0
    
    try {
      setRefreshing(true)
      const rec = await api.getRecording(recordingId)
      setRecording(rec)
      if (rec.status === 'completed') {
        const [evalRes, transcriptRes, dl] = await Promise.all([
          api.getEvaluation(recordingId),
          api.getTranscript(recordingId).catch(() => null),
          api.getDownloadUrl(recordingId).catch(() => null),
        ])
        setEvaluation(evalRes)
        if (transcriptRes) setTranscript(transcriptRes)
        if (dl?.download_url) setAudioUrl(dl.download_url)
        try {
          // Use fresh templates on refresh
          const templates = await api.getTemplates()
          templatesCache = templates
          templatesCacheTime = Date.now()
          const tpl = templates.find(t => t.id === evalRes.policy_template_id) || null
          setPolicyTemplate(tpl)
        } catch {
          // ignore
        }
      }
    } catch (e: any) {
      setError(e.message || 'Failed to refresh results')
    } finally {
      setRefreshing(false)
    }
  }

  const handleReevaluate = async () => {
    if (!recordingId) return
    if (!confirm('This will re-evaluate the recording. Continue?')) return
    try {
      await api.reevaluateRecording(recordingId)
      alert('Re-evaluation started. Please return later or refresh to check status.')
      navigate('/demo')
    } catch (e: any) {
      alert('Failed to start re-evaluation: ' + (e.message || 'Unknown error'))
    }
  }

  const createTestHumanReview = async () => {
    if (!evaluation) return

    try {
      setCreatingReview(true)
      await api.createTestHumanReview(evaluation.id)
      alert('Test human review created! Check the Human Review page to see it in the queue.')
    } catch (error) {
      console.error('Failed to create test human review:', error)
      alert('Failed to create test human review. Make sure this evaluation doesn\'t already have a pending review.')
    } finally {
      setCreatingReview(false)
    }
  }

  // Exports
  const downloadTranscriptTxt = () => {
    if (!transcript) return
    const text = transcript.diarized_segments && transcript.diarized_segments.length > 0
      ? transcript.diarized_segments.map(s => `[${s.speaker}] ${s.text}`).join('\n')
      : (transcript.transcript_text || '')
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${recording?.file_name || 'transcript'}.txt`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const downloadScoresCsv = () => {
    if (!evaluation?.category_scores?.length) return
    const rows = [
      ['Category', 'Score', 'Feedback'],
      ...evaluation.category_scores.map(cs => [cs.category_name, String(cs.score), (cs.feedback || '').replace(/\n/g, ' ')])
    ]
    const csv = rows.map(r => r.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${recording?.file_name || 'results'}_category_scores.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const downloadViolationsCsv = () => {
    if (!evaluation?.policy_violations?.length) return
    const rows = [
      ['Violation Type', 'Severity', 'Description', 'Criteria ID'],
      ...evaluation.policy_violations.map(v => [v.violation_type, v.severity, v.description.replace(/\n/g, ' '), v.criteria_id])
    ]
    const csv = rows.map(r => r.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${recording?.file_name || 'results'}_violations.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen relative">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-400/8 dark:bg-brand-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/3 left-0 w-96 h-96 bg-green-400/8 dark:bg-green-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Link
              to="/demo"
              className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600"
            >
              <FaArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Results</h1>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
            >
              <FaSpinner className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <div className="hidden md:flex items-center space-x-2">
              <button
                onClick={downloadTranscriptTxt}
                disabled={!transcript}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <FaFileAlt className="w-4 h-4 mr-2" />
                Transcript
              </button>
              <button
                onClick={downloadScoresCsv}
                disabled={!evaluation?.category_scores?.length}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <FaFileCsv className="w-4 h-4 mr-2" />
                Scores CSV
              </button>
              <button
                onClick={downloadViolationsCsv}
                disabled={!evaluation?.policy_violations?.length}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <FaFileCsv className="w-4 h-4 mr-2" />
                Violations CSV
              </button>
            </div>
            <button
              onClick={handleReevaluate}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Retest
            </button>
          </div>
        </div>

        {loading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 border border-gray-200 dark:border-gray-700 text-center">
            <FaSpinner className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
          </div>
        ) : error ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-red-200 dark:border-red-800">
            <div className="flex items-center space-x-2 text-red-700 dark:text-red-300">
              <FaExclamationCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        ) : !recording ? null : recording.status !== 'completed' ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 border border-gray-200 dark:border-gray-700 text-center">
            <div className="mx-auto flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/50 rounded-full mb-4">
              <FaSpinner className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              Processing in progress
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              Current status: <span className="font-medium">{recording.status}</span>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-1 space-y-8">
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Recording
                  </h2>
                </div>
                <div className="p-6">
                  <p className="text-sm text-slate-700 dark:text-slate-300 font-medium break-words">
                    {recording.file_name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Uploaded: {new Date(recording.uploaded_at).toLocaleString()}
                  </p>
                  {recording.duration_seconds != null && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Duration: {formatTime(recording.duration_seconds)}
                    </p>
                  )}

                  {audioUrl && (
                    <div className="mt-4">
                      <div className="flex items-center space-x-3 mb-2">
                        <button
                          onClick={() => {
                            if (!audioRef.current) return
                            if (isPlaying) {
                              audioRef.current.pause()
                            } else {
                              audioRef.current.play()
                            }
                            setIsPlaying(!isPlaying)
                          }}
                          className="w-10 h-10 bg-blue-600 text-white rounded-full hover:bg-blue-700 flex items-center justify-center transition-colors"
                        >
                          {isPlaying ? <FaPause className="w-4 h-4" /> : <FaPlay className="w-4 h-4" />}
                        </button>
                        <div className="flex items-center text-sm text-slate-600 dark:text-slate-300">
                          <FaVolumeUp className="w-4 h-4 mr-2" />
                          Listen
                        </div>
                      </div>
                      <audio ref={audioRef} controls className="w-full">
                        <source src={audioUrl} />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  )}
                </div>
              </div>

              {policyTemplate && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Policy Template
                    </h2>
                  </div>
                  <div className="p-6">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {policyTemplate.template_name}
                    </p>
                    {policyTemplate.description && (
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                        {policyTemplate.description}
                      </p>
                    )}
                    <div className="mt-4">
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                        Criteria (Weights must sum to 100%)
                      </h4>
                      <div className="space-y-2">
                        {policyTemplate.criteria.map(c => (
                          <div key={c.id} className="p-3 rounded border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-slate-900 dark:text-white">{c.category_name}</span>
                              <span className="text-xs text-slate-600 dark:text-slate-300">{c.weight}% • Pass ≥ {c.passing_score}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Overall Score
                  </h2>
                </div>
                <div className="p-6 text-center">
                  <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full mb-4">
                    <span className="text-2xl font-bold text-white">
                      {evaluation?.overall_score ?? '--'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 flex items-center justify-center">
                    <FaChartBar className="w-4 h-4 mr-2 text-blue-600" />
                    Quality Score
                  </p>
                  {evaluation && (
                    <button
                      onClick={createTestHumanReview}
                      disabled={creatingReview}
                      className="mt-4 px-4 py-2 bg-orange-500 hover:bg-orange-600 disabled:bg-orange-400 text-white text-sm rounded-lg transition-colors flex items-center justify-center"
                    >
                      {creatingReview ? (
                        <>
                          <FaSpinner className="animate-spin w-4 h-4 mr-2" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <FaExclamationCircle className="w-4 h-4 mr-2" />
                          Test Human Review
                        </>
                      )}
                    </button>
                  )}
                  <div className="grid grid-cols-2 gap-4 max-w-md mx-auto mt-4">
                    <div className="text-center">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        evaluation?.resolution_detected
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {evaluation?.resolution_detected ? 'Resolved' : 'Unresolved'}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Issue Status</p>
                    </div>
                    <div className="text-center">
                      <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                        {evaluation ? `${(evaluation.resolution_confidence * 100).toFixed(0)}%` : '--'} Confidence
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Resolution Confidence</p>
                    </div>
                  </div>
                </div>
              </div>

              {evaluation?.customer_tone && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Customer Analysis
                    </h2>
                  </div>
                  <div className="p-6">
                    <div className="mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          Primary Emotion
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300">
                          {evaluation.customer_tone.primary_emotion}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                        {evaluation.customer_tone.description}
                      </p>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Analysis Confidence: {(evaluation.customer_tone.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                    {evaluation.customer_tone.emotional_journey && evaluation.customer_tone.emotional_journey.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                          Call Journey
                        </h4>
                        <div className="space-y-2">
                          {evaluation.customer_tone.emotional_journey.map((j, i) => (
                            <div key={i} className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-700/50 rounded border border-slate-200 dark:border-slate-600">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase">{j.segment}</span>
                                <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300">
                                  {j.emotion}
                                </span>
                              </div>
                              <span className="text-xs text-slate-500 dark:text-slate-400">{j.intensity}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="xl:col-span-2 space-y-8">
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Category Performance</h3>
                </div>
                <div className="p-6">
                  {evaluation?.category_scores?.length ? (
                    <div className="space-y-4">
                      {evaluation.category_scores.map((c) => (
                        <div key={c.id} className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-medium text-slate-900 dark:text-white">{c.category_name}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-lg font-bold text-slate-900 dark:text-white">{c.score}</span>
                              <span className="text-sm text-slate-600 dark:text-slate-400">/100</span>
                            </div>
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-3">
                            <div
                              className="h-2 rounded-full transition-all bg-blue-500"
                              style={{ width: `${c.score}%` }}
                            />
                          </div>
                          {c.feedback && (
                            <p className="text-sm text-slate-600 dark:text-slate-400">{c.feedback}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-600 dark:text-slate-400">No category scores found.</p>
                  )}
                </div>
              </div>

              {evaluation?.policy_violations?.length ? (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
                      <FaExclamationCircle className="w-5 h-5 text-red-600" />
                      <span>Issues Identified</span>
                    </h3>
                  </div>
                  <div className="p-6">
                    <div className="space-y-3">
                      {evaluation.policy_violations.map((v) => (
                        <div key={v.id} className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium text-red-900 dark:text-red-200">
                                {v.violation_type}
                              </span>
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200">
                                {v.severity}
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-red-700 dark:text-red-300">{v.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}

              {evaluation?.llm_analysis && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <button
                    onClick={() => setShowAnalysis(!showAnalysis)}
                    className="w-full px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between text-left"
                  >
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">LLM Analysis Details</h3>
                    {showAnalysis ? <FaChevronDown className="w-4 h-4 text-slate-500" /> : <FaChevronRight className="w-4 h-4 text-slate-500" />}
                  </button>
                  {showAnalysis && (
                    <div className="p-6">
                      <pre className="text-xs bg-slate-900 text-slate-100 rounded p-4 overflow-auto max-h-96">
                        {JSON.stringify(evaluation.llm_analysis, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Conversation Transcript</h3>
                </div>
                <div className="p-6">
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                    {transcript?.diarized_segments && transcript.diarized_segments.length > 0 ? (
                      <div className="space-y-4">
                        {transcript.diarized_segments.map((segment, index) => {
                          const isCaller = segment.speaker === 'caller'
                          const isAgent = segment.speaker === 'agent' || segment.speaker.startsWith('agent')
                          const speakerLabel = isCaller ? 'Customer' : isAgent ? 'Agent' : segment.speaker
                          return (
                            <div
                              key={index}
                              className={`p-3 rounded-lg border-l-4 ${
                                isCaller
                                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                                  : isAgent
                                  ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-500'
                                  : 'bg-violet-50 dark:bg-violet-900/20 border-violet-500'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className={`text-xs font-semibold uppercase tracking-wider ${
                                  isCaller
                                    ? 'text-blue-800 dark:text-blue-200'
                                    : isAgent
                                    ? 'text-emerald-800 dark:text-emerald-200'
                                    : 'text-violet-800 dark:text-violet-200'
                                }`}>
                                  {speakerLabel}
                                </span>
                                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                                  {formatTime(segment.start)} - {formatTime(segment.end)}
                                </span>
                              </div>
                              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                {segment.text}
          </p>
        </div>
                          )
                        })}
                      </div>
                    ) : (
                      <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                        {transcript?.transcript_text || 'Transcript not available'}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

