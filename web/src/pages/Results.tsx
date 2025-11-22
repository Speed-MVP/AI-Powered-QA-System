import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaArrowLeft, FaChartBar, FaExclamationCircle, FaPlay, FaPause, FaSpinner, FaVolumeUp, FaChevronDown, FaChevronRight, FaFileCsv, FaFileAlt, FaCheckCircle, FaTimesCircle, FaShieldAlt, FaBrain, FaRobot } from 'react-icons/fa'
import { ConfirmModal, AlertModal } from '@/components/modals'

type EvaluationResponse = Awaited<ReturnType<typeof api.getEvaluation>>
type TranscriptResponse = Awaited<ReturnType<typeof api.getTranscript>>
type RecordingResponse = Awaited<ReturnType<typeof api.getRecording>>

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
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [creatingReview, setCreatingReview] = useState(false)
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; title: string; message: string; onConfirm: () => void } | null>(null)
  const [alertModal, setAlertModal] = useState<{ isOpen: boolean; title: string; message: string; type: 'success' | 'error' | 'info' } | null>(null)

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
      }
    } catch (e: any) {
      setError(e.message || 'Failed to refresh results')
    } finally {
      setRefreshing(false)
    }
  }

  const handleReevaluate = () => {
    if (!recordingId) return
    setConfirmModal({
      isOpen: true,
      title: 'Re-evaluate Recording',
      message: 'This will re-evaluate the recording. Continue?',
      onConfirm: async () => {
        setConfirmModal(null)
        try {
          await api.reevaluateRecording(recordingId)
          setAlertModal({
            isOpen: true,
            title: 'Re-evaluation Started',
            message: 'Re-evaluation started. Please return later or refresh to check status.',
            type: 'success',
          })
          setTimeout(() => navigate('/demo'), 2000)
        } catch (e: any) {
          setAlertModal({
            isOpen: true,
            title: 'Error',
            message: 'Failed to start re-evaluation: ' + (e.message || 'Unknown error'),
            type: 'error',
          })
        }
      },
    })
  }

  const createTestHumanReview = async () => {
    if (!evaluation) return

    try {
      setCreatingReview(true)
      await api.createTestHumanReview(evaluation.id)
      setAlertModal({
        isOpen: true,
        title: 'Success',
        message: 'Test human review created! Check the Human Review page to see it in the queue.',
        type: 'success',
      })
    } catch (error: any) {
      console.error('Failed to create test human review:', error)
      setAlertModal({
        isOpen: true,
        title: 'Error',
        message: 'Failed to create test human review. Make sure this evaluation doesn\'t already have a pending review.',
        type: 'error',
      })
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
    // Check for Phase 7 final_evaluation first, then fall back to legacy category_scores
    const categoryScores = evaluation?.final_evaluation?.category_scores || evaluation?.category_scores
    if (!categoryScores?.length) return
    
    const rows = [
      ['Category', 'Score', 'Weight', 'Passed', 'Feedback'],
      ...categoryScores.map((cs: any) => [
        cs.name || cs.category_name,
        String(cs.score),
        cs.weight ? `${cs.weight}%` : '',
        cs.passed !== undefined ? (cs.passed ? 'Yes' : 'No') : '',
        (cs.feedback || '').replace(/\n/g, ' ')
      ])
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
                disabled={!(evaluation?.final_evaluation?.category_scores?.length || evaluation?.category_scores?.length)}
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


              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Overall Score
                  </h2>
                </div>
                <div className="p-6 text-center">
                  <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-4 ${
                    evaluation?.final_evaluation?.overall_passed === false
                      ? 'bg-gradient-to-br from-red-500 to-red-600'
                      : evaluation?.final_evaluation?.overall_passed === true
                      ? 'bg-gradient-to-br from-green-500 to-green-600'
                      : 'bg-gradient-to-br from-blue-500 to-indigo-600'
                  }`}>
                    <span className="text-2xl font-bold text-white">
                      {evaluation?.overall_score ?? '--'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 flex items-center justify-center">
                    <FaChartBar className="w-4 h-4 mr-2 text-blue-600" />
                    Quality Score
                  </p>
                  {evaluation?.final_evaluation && (
                    <div className="mt-2">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        evaluation.final_evaluation.overall_passed
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {evaluation.final_evaluation.overall_passed ? 'Passed' : 'Failed'}
                      </span>
                      {evaluation.final_evaluation.requires_human_review && (
                        <p className="text-xs text-orange-600 dark:text-orange-400 mt-2 flex items-center justify-center gap-1">
                          <FaExclamationCircle className="w-3 h-3" />
                          Requires Human Review
                        </p>
                      )}
                    </div>
                  )}
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
              {/* Phase 7: Final Evaluation Display */}
              {evaluation?.final_evaluation ? (
                <>
                  {/* Category Scores from Final Evaluation */}
                  <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                        <FaChartBar className="w-5 h-5" />
                        Category Performance
                      </h3>
                    </div>
                    <div className="p-6">
                      {evaluation.final_evaluation.category_scores?.length ? (
                        <div className="space-y-4">
                          {evaluation.final_evaluation.category_scores.map((cat: any, idx: number) => (
                            <div key={cat.category_id || idx} className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-slate-900 dark:text-white">{cat.name}</span>
                                  <span className="text-xs px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300">
                                    {cat.weight}% weight
                                  </span>
                                  {cat.passed ? (
                                    <FaCheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                                  ) : (
                                    <FaTimesCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                                  )}
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className={`text-lg font-bold ${
                                    cat.passed 
                                      ? 'text-green-600 dark:text-green-400' 
                                      : 'text-red-600 dark:text-red-400'
                                  }`}>
                                    {cat.score}
                                  </span>
                                  <span className="text-sm text-slate-600 dark:text-slate-400">/100</span>
                                </div>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-2">
                                <div
                                  className={`h-2 rounded-full transition-all ${
                                    cat.passed ? 'bg-green-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${cat.score}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-slate-600 dark:text-slate-400">No category scores found.</p>
                      )}
                    </div>
                  </div>

                  {/* Stage Scores Breakdown */}
                  {evaluation.final_evaluation.stage_scores && Object.keys(evaluation.final_evaluation.stage_scores).length > 0 && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                          <FaRobot className="w-5 h-5" />
                          Stage Evaluations
                        </h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-4">
                          {Object.entries(evaluation.final_evaluation.stage_scores).map(([stageId, stageData]: [string, any]) => {
                            const llmStageEval = evaluation.llm_stage_evaluations?.[stageId]
                            return (
                              <div key={stageId} className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-slate-900 dark:text-white">
                                      {llmStageEval?.stage_name || `Stage ${stageId.slice(0, 8)}`}
                                    </span>
                                    {stageData.critical_violation && (
                                      <span className="text-xs px-2 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                                        Critical
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <span className="text-lg font-bold text-slate-900 dark:text-white">{stageData.score}</span>
                                    <span className="text-sm text-slate-600 dark:text-slate-400">/100</span>
                                    <span className="text-xs text-slate-500 dark:text-slate-400">
                                      {(stageData.confidence * 100).toFixed(0)}% conf
                                    </span>
                                  </div>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-3">
                                  <div
                                    className="h-2 rounded-full transition-all bg-blue-500"
                                    style={{ width: `${stageData.score}%` }}
                                  />
                                </div>
                                
                                {/* Step Evaluations */}
                                {llmStageEval?.step_evaluations?.length > 0 && (
                                  <div className="mt-3 space-y-2">
                                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Steps:</h4>
                                    {llmStageEval.step_evaluations.map((stepEval: any, stepIdx: number) => (
                                      <div key={stepEval.step_id || stepIdx} className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-600">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-2">
                                            {stepEval.passed ? (
                                              <FaCheckCircle className="w-3 h-3 text-green-600 dark:text-green-400" />
                                            ) : (
                                              <FaTimesCircle className="w-3 h-3 text-red-600 dark:text-red-400" />
                                            )}
                                            <span className="text-sm text-slate-700 dark:text-slate-300">
                                              {stepEval.step_name || `Step ${stepEval.step_id?.slice(0, 8)}`}
                                            </span>
                                          </div>
                                          <span className={`text-xs px-2 py-0.5 rounded ${
                                            stepEval.passed
                                              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                                              : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                                          }`}>
                                            {stepEval.passed ? 'Passed' : 'Failed'}
                                          </span>
                                        </div>
                                        {stepEval.rationale && (
                                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">{stepEval.rationale}</p>
                                        )}
                                        {stepEval.evidence?.length > 0 && (
                                          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                                            <span className="font-medium">Evidence:</span>
                                            <ul className="list-disc list-inside ml-2 mt-1">
                                              {stepEval.evidence.map((ev: any, evIdx: number) => (
                                                <li key={evIdx}>
                                                  {ev.type === 'transcript_snippet' && ev.text && (
                                                    <span className="italic">"{ev.text}"</span>
                                                  )}
                                                  {ev.type === 'rule_evidence' && ev.rule_id && (
                                                    <span>Rule {ev.rule_id.slice(0, 8)}</span>
                                                  )}
                                                </li>
                                              ))}
                                            </ul>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                                
                                {/* Stage Feedback */}
                                {llmStageEval?.stage_feedback?.length > 0 && (
                                  <div className="mt-3">
                                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Feedback:</h4>
                                    <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400 space-y-1">
                                      {llmStageEval.stage_feedback.map((fb: string, fbIdx: number) => (
                                        <li key={fbIdx}>{fb}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Deterministic Rule Results */}
                  {evaluation.deterministic_results?.rule_evaluations?.length > 0 && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                          <FaShieldAlt className="w-5 h-5" />
                          Compliance Rules
                        </h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-3">
                          {evaluation.deterministic_results.rule_evaluations.map((rule: any, idx: number) => (
                            <div key={rule.rule_id || idx} className={`p-3 rounded-lg border ${
                              rule.passed
                                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                                : `bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800`
                            }`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  {rule.passed ? (
                                    <FaCheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                                  ) : (
                                    <FaTimesCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                                  )}
                                  <span className="font-medium text-slate-900 dark:text-white">{rule.rule_title || rule.rule_id}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded ${
                                    rule.severity === 'critical'
                                      ? 'bg-red-200 dark:bg-red-800 text-red-900 dark:text-red-200'
                                      : rule.severity === 'major'
                                      ? 'bg-orange-200 dark:bg-orange-800 text-orange-900 dark:text-orange-200'
                                      : 'bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-200'
                                  }`}>
                                    {rule.severity || 'minor'}
                                  </span>
                                </div>
                                <span className={`text-sm font-medium ${
                                  rule.passed
                                    ? 'text-green-700 dark:text-green-300'
                                    : 'text-red-700 dark:text-red-300'
                                }`}>
                                  {rule.passed ? 'Passed' : 'Failed'}
                                </span>
                              </div>
                              {rule.evidence && (
                                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">{rule.evidence}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Legacy Category Scores Display */
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
              )}

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

      {/* Confirm Modal */}
      {confirmModal && (
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          onClose={() => setConfirmModal(null)}
          onConfirm={confirmModal.onConfirm}
          title={confirmModal.title}
          message={confirmModal.message}
          confirmText="Continue"
          cancelText="Cancel"
          confirmColor="blue"
        />
      )}

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

