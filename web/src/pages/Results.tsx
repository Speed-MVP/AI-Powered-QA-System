import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaArrowLeft, FaChartBar, FaExclamationCircle, FaPlay, FaPause, FaSpinner, FaVolumeUp, FaFileCsv, FaFileAlt, FaCheckCircle, FaTimesCircle } from 'react-icons/fa'
import { ConfirmModal, AlertModal } from '@/components/modals'

type EvaluationResponse = Awaited<ReturnType<typeof api.getEvaluation>>
type TranscriptResponse = Awaited<ReturnType<typeof api.getTranscript>>
type RecordingResponse = Awaited<ReturnType<typeof api.getRecording>>

export function Results() {
  const { recordingId } = useParams<{ recordingId: string }>()
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
  const [piiBlocked, setPiiBlocked] = useState<string | null>(null)
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

        // Surface PII/redaction-blocked failures explicitly
        if (rec.status === 'failed') {
          const msg = rec.error_message || 'Evaluation failed.'
          if (msg.toLowerCase().includes('pii') || msg.toLowerCase().includes('redaction')) {
            setPiiBlocked(msg)
            setError(null)
          } else {
            setError(msg)
          }
          setLoading(false)
          isLoadingRef.current = false
          return
        }

        if (rec.status !== 'completed') {
          setLoading(false)
          isLoadingRef.current = false
          return
        }

        // Fetch all data in parallel (include explanation in evaluation)
        const [evalRes, transcriptRes, dl] = await Promise.all([
          api.getEvaluation(recordingId, { include_explanation: true }),
          api.getTranscript(recordingId).catch(() => null),
          api.getDownloadUrl(recordingId).catch(() => null),
        ])

        // Check if request was aborted
        if (abortController.signal.aborted) return

        setEvaluation(evalRes)
        if (transcriptRes) setTranscript(transcriptRes)
        if (dl?.download_url) setAudioUrl(dl.download_url)
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
          api.getEvaluation(recordingId, { include_explanation: true }),
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
    const stageScores = evaluation?.stage_scores
    
    // Convert stage_scores to rows
    const rows = [
      ['Stage', 'Score', 'Weight', 'Passed', 'Feedback'],
    ]
    
    if (stageScores && Array.isArray(stageScores) && stageScores.length > 0) {
      rows.push(...stageScores.map((stage: any) => [
        stage.stage_name || stage.name || 'Unknown Stage',
        String(stage.score || 0),
        stage.weight ? `${stage.weight}%` : '',
        stage.passed !== undefined ? (stage.passed ? 'Yes' : 'No') : '',
        (stage.feedback || '').replace(/\n/g, ' ')
      ]))
    } else if (stageScores && typeof stageScores === 'object' && !Array.isArray(stageScores)) {
      // Handle object format
      rows.push(...Object.entries(stageScores).map(([stageId, stage]: [string, any]) => [
        stage.stage_name || stage.name || stageId,
        String(stage.score || 0),
        stage.weight ? `${stage.weight}%` : '',
        stage.passed !== undefined ? (stage.passed ? 'Yes' : 'No') : '',
        (stage.feedback || '').replace(/\n/g, ' ')
      ]))
    } else {
      return // No scores to export
    }
    
    const csv = rows.map(r => r.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${recording?.file_name || 'results'}_scores.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const downloadViolationsCsv = () => {
    const violations = evaluation?.policy_violations || []
    if (!violations.length) return
    
    const rows = [
      ['Type', 'Severity', 'Description', 'Rule ID'],
      ...violations.map((v: any) => [
        v.type || v.violation_type || '',
        v.severity || 'minor',
        (v.description || '').replace(/\n/g, ' '),
        v.rule_id || v.criteria_id || ''
      ])
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

  const explanation = (evaluation as any)?.explanation as any | undefined
  const confidenceBreakdown = (evaluation as any)?.confidence_breakdown as any | undefined

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
                disabled={!(
                  (evaluation?.stage_scores && evaluation.stage_scores.length > 0)
                )}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <FaFileCsv className="w-4 h-4 mr-2" />
                Scores CSV
              </button>
              <button
                onClick={downloadViolationsCsv}
                disabled={!(
                  (evaluation?.policy_violations && evaluation.policy_violations.length > 0)
                )}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <FaFileCsv className="w-4 h-4 mr-2" />
                Violations CSV
              </button>
            </div>
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
        ) : piiBlocked ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 border border-orange-200 dark:border-orange-800">
            <div className="flex items-center space-x-3 text-orange-700 dark:text-orange-300">
              <FaExclamationCircle className="w-6 h-6" />
              <div>
                <h3 className="text-lg font-semibold">Evaluation blocked for privacy</h3>
                <p className="text-sm mt-1">
                  {piiBlocked}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                  No data was sent to the model. Please remove sensitive info or route to a human reviewer.
                </p>
              </div>
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
                    evaluation?.overall_passed === false
                      ? 'bg-gradient-to-br from-red-500 to-red-600'
                      : evaluation?.overall_passed === true
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
                  {evaluation?.requires_human_review && (
                    <div className="mt-2">
                      <p className="text-xs text-orange-600 dark:text-orange-400 flex items-center justify-center gap-1">
                        <FaExclamationCircle className="w-3 h-3" />
                        Requires Human Review
                      </p>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4 max-w-md mx-auto mt-4">
                    <div className="text-center">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        evaluation?.overall_passed
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {evaluation?.overall_passed ? 'Passed' : 'Failed'}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Overall Result</p>
                    </div>
                    <div className="text-center">
                      <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                        {evaluation?.confidence_score ? `${(evaluation.confidence_score * 100).toFixed(0)}%` : '--'} Confidence
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Evaluation Confidence</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="xl:col-span-2 space-y-8">
              {/* Explanation Panel */}
              {explanation && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                      <FaChartBar className="w-5 h-5" />
                      Why this score?
                    </h3>
                  </div>
                  <div className="p-6 space-y-4">
                    {/* Overall explanation */}
                    {explanation.overall_explanation && (
                      <div>
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {explanation.overall_explanation.breakdown}
                        </p>
                        {Array.isArray(explanation.overall_explanation.stage_contributions) && (
                          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            {explanation.overall_explanation.stage_contributions.map((c: any, idx: number) => (
                              <div key={idx} className="p-2 bg-slate-50 dark:bg-slate-900/40 rounded border border-slate-200 dark:border-slate-700">
                                <div className="flex justify-between items-center">
                                  <span className="font-medium text-slate-900 dark:text-slate-100">
                                    {c.stage}
                                  </span>
                                  <span className="text-slate-600 dark:text-slate-300">
                                    {c.score}/100 · {c.weight?.toFixed ? c.weight.toFixed(1) : c.weight}% weight
                                  </span>
                                </div>
                                <p className="mt-1 text-slate-600 dark:text-slate-400">
                                  Contribution ≈ {c.contribution?.toFixed ? c.contribution.toFixed(1) : c.contribution} pts
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Confidence breakdown */}
                    {confidenceBreakdown && confidenceBreakdown.signals && (
                      <div className="mt-4">
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-2">
                          Confidence signals
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {Object.entries(confidenceBreakdown.signals).map(([name, value]: [string, any]) => (
                            <div
                              key={name}
                              className="p-2 bg-slate-50 dark:bg-slate-900/40 rounded border border-slate-200 dark:border-slate-700 text-xs"
                            >
                              <div className="flex justify-between mb-1">
                                <span className="font-medium text-slate-800 dark:text-slate-100">
                                  {name.replace(/_/g, ' ')}
                                </span>
                                <span className="text-slate-600 dark:text-slate-300">
                                  {Math.round((value as number) * 100)}%
                                </span>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                                <div
                                  className="h-1.5 rounded-full bg-blue-500"
                                  style={{ width: `${Math.min(100, Math.max(0, (value as number) * 100))}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                        {confidenceBreakdown.reasoning && (
                          <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                            {confidenceBreakdown.reasoning}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
              {/* Stage Scores (Blueprint-based) */}
              {evaluation?.stage_scores && Array.isArray(evaluation.stage_scores) && evaluation.stage_scores.length > 0 ? (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                          <FaChartBar className="w-5 h-5" />
                          Stage Performance
                        </h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-4">
                          {evaluation.stage_scores.map((stage: any, idx: number) => (
                            <div key={stage.stage_id || stage.stage_name || idx} className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-slate-900 dark:text-white">
                                    {stage.stage_name || stage.name || `Stage ${idx + 1}`}
                                  </span>
                                  {stage.passed !== undefined && (
                                    stage.passed ? (
                                      <FaCheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                                    ) : (
                                      <FaTimesCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                                    )
                                  )}
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className={`text-lg font-bold ${
                                    stage.passed 
                                      ? 'text-green-600 dark:text-green-400' 
                                      : stage.passed === false
                                      ? 'text-red-600 dark:text-red-400'
                                      : 'text-slate-600 dark:text-slate-400'
                                  }`}>
                                    {stage.score || 0}
                                  </span>
                                  <span className="text-sm text-slate-600 dark:text-slate-400">/100</span>
                                </div>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-2">
                                <div
                                  className={`h-2 rounded-full transition-all ${
                                    (stage.score || 0) >= 90 ? 'bg-green-500' :
                                    (stage.score || 0) >= 70 ? 'bg-blue-500' :
                                    (stage.score || 0) >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${Math.min(stage.score || 0, 100)}%` }}
                                />
                              </div>
                              {stage.feedback && (
                                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">{stage.feedback}</p>
                              )}
                              {stage.behaviors && stage.behaviors.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600">
                                  <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Behaviors:</p>
                                  <div className="space-y-1">
                                    {stage.behaviors.map((behavior: any, bIdx: number) => (
                                      <div key={bIdx} className="text-xs text-slate-600 dark:text-slate-400">
                                        • {behavior.behavior_name}: {behavior.satisfaction_level} ({Math.round((behavior.confidence || 0) * 100)}% confidence)
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : null}

              {/* Policy Violations (Blueprint-based) */}
              {evaluation?.policy_violations && evaluation.policy_violations.length > 0 ? (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
                      <FaExclamationCircle className="w-5 h-5 text-red-600" />
                      <span>Policy Violations</span>
                    </h3>
                  </div>
                  <div className="p-6">
                    <div className="space-y-3">
                      {evaluation.policy_violations.map((v: any, idx: number) => (
                        <div key={v.id || v.rule_id || idx} className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium text-red-900 dark:text-red-200">
                                {v.type || v.violation_type || 'Policy Violation'}
                              </span>
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                (v.severity || 'minor') === 'critical'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200'
                                  : (v.severity || 'minor') === 'major'
                                  ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200'
                                  : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200'
                              }`}>
                                {v.severity || 'minor'}
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-red-700 dark:text-red-300">{v.description}</p>
                          {v.timestamp && (
                            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                              Time: {new Date(v.timestamp * 1000).toLocaleTimeString()}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}


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



