import { useCallback, useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { FaCloudUploadAlt, FaCheckCircle, FaSpinner, FaFileAudio, FaPlay, FaChartBar, FaCog, FaExclamationCircle, FaTrash, FaRedo, FaVolumeUp, FaPause, FaHistory, FaTimes, FaUser } from 'react-icons/fa'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'

interface UploadedFile {
  id: string
  name: string
  size: number
  file: File
  status: 'uploading' | 'uploaded' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
  recordingId?: string
}

interface ProcessingResult {
  transcript: string
  diarizedSegments?: Array<{
    speaker: string
    text: string
    start: number
    end: number
  }> | null
  overallScore: number
  resolutionDetected: boolean
  resolutionConfidence: number
  customerTone?: {
    primary_emotion: string
    confidence: number
    description: string
    emotional_journey?: Array<{
      segment: string
      emotion: string
      intensity: string
      evidence: string
    }>
  }
  categoryScores: {
    category: string
    score: number
    feedback: string
  }[]
  violations: {
    type: string
    severity: 'critical' | 'major' | 'minor'
    description: string
    timestamp?: number
  }[]
}

interface RecordingHistory {
  id: string
  file_name: string
  file_url: string
  status: string
  uploaded_at: string
  processed_at: string | null
  duration_seconds: number | null
  error_message: string | null
}

export function Test() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [history, setHistory] = useState<RecordingHistory[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedRecordingId, setSelectedRecordingId] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [showHistory, setShowHistory] = useState(false)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  // Load recording history
  const loadHistory = async () => {
    try {
      setLoadingHistory(true)
      const recordings = await api.listRecordings({ limit: 50 })
      setHistory(recordings)
    } catch (error: any) {
      console.error('Failed to load history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Load history on mount
  useEffect(() => {
    loadHistory()
  }, [])

  // Load audio URL for playback
  const loadAudioUrl = async (recordingId: string) => {
    try {
      const { download_url } = await api.getDownloadUrl(recordingId)
      setAudioUrl(download_url)
      setSelectedRecordingId(recordingId)
      if (audioRef.current) {
        audioRef.current.src = download_url
        audioRef.current.load()
      }
    } catch (error: any) {
      console.error('Failed to load audio URL:', error)
      alert('Failed to load audio file')
    }
  }

  // Handle audio play/pause
  const toggleAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  // Handle audio ended
  useEffect(() => {
    const audio = audioRef.current
    if (audio) {
      audio.addEventListener('ended', () => setIsPlaying(false))
      audio.addEventListener('play', () => setIsPlaying(true))
      audio.addEventListener('pause', () => setIsPlaying(false))
      return () => {
        audio.removeEventListener('ended', () => setIsPlaying(false))
        audio.removeEventListener('play', () => setIsPlaying(true))
        audio.removeEventListener('pause', () => setIsPlaying(false))
      }
    }
  }, [audioUrl])

  // Delete recording
  const handleDeleteRecording = async (recordingId: string) => {
    if (!confirm('Are you sure you want to delete this recording? This will permanently delete the file from storage.')) {
      return
    }

    try {
      await api.deleteRecording(recordingId)
      setHistory(prev => prev.filter(r => r.id !== recordingId))
      if (selectedRecordingId === recordingId) {
        setSelectedRecordingId(null)
        setAudioUrl(null)
        setResult(null)
      }
      alert('Recording deleted successfully')
    } catch (error: any) {
      console.error('Failed to delete recording:', error)
      alert('Failed to delete recording: ' + (error.message || 'Unknown error'))
    }
  }

  // Reevaluate recording
  const handleReevaluate = async (recordingId: string) => {
    if (!confirm('This will re-evaluate the recording. Continue?')) {
      return
    }

    try {
      await api.reevaluateRecording(recordingId)
      alert('Re-evaluation started. Please wait for processing to complete.')
      // Reload history to update status
      await loadHistory()
      // If this is the selected recording, start polling for results
      const recording = history.find(r => r.id === recordingId)
      if (recording) {
        setIsProcessing(true)
        setResult(null)
        // Poll for results
        const poll = async () => {
          try {
            const updated = await api.getRecording(recordingId)
            if (updated.status === 'completed') {
              // Load results
              const evaluation = await api.getEvaluation(recordingId)
              const transcriptData = await api.getTranscript(recordingId)
              
              const processingResult: ProcessingResult = {
                transcript: transcriptData.transcript_text,
                diarizedSegments: transcriptData.diarized_segments || null,
                overallScore: evaluation.overall_score,
                resolutionDetected: evaluation.resolution_detected,
                resolutionConfidence: evaluation.resolution_confidence,
                categoryScores: evaluation.category_scores.map(cs => ({
                  category: cs.category_name,
                  score: cs.score,
                  feedback: cs.feedback || ''
                })),
                violations: evaluation.policy_violations.map(v => ({
                  type: v.violation_type,
                  severity: v.severity as 'critical' | 'major' | 'minor',
                  description: v.description
                }))
              }
              
              setResult(processingResult)
              setIsProcessing(false)
              await loadHistory()
            } else if (updated.status === 'failed') {
              alert('Re-evaluation failed: ' + (updated.error_message || 'Unknown error'))
              setIsProcessing(false)
              await loadHistory()
            } else {
              // Continue polling
              setTimeout(poll, 5000)
            }
          } catch (error: any) {
            console.error('Polling error:', error)
            setIsProcessing(false)
          }
        }
        poll()
      }
    } catch (error: any) {
      console.error('Failed to reevaluate:', error)
      alert('Failed to start re-evaluation: ' + (error.message || 'Unknown error'))
    }
  }

  // Load recording results
  const loadRecordingResults = async (recordingId: string) => {
    try {
      setIsProcessing(true)
      setResult(null)
      setSelectedRecordingId(recordingId)
      
      const recording = await api.getRecording(recordingId)
      if (recording.status === 'completed') {
        const evaluation = await api.getEvaluation(recordingId)
        const transcriptData = await api.getTranscript(recordingId)
        
        const processingResult: ProcessingResult = {
          transcript: transcriptData.transcript_text,
          diarizedSegments: transcriptData.diarized_segments || null,
          overallScore: evaluation.overall_score,
          resolutionDetected: evaluation.resolution_detected,
          resolutionConfidence: evaluation.resolution_confidence,
          categoryScores: evaluation.category_scores.map(cs => ({
            category: cs.category_name,
            score: cs.score,
            feedback: cs.feedback || ''
          })),
          violations: evaluation.policy_violations.map(v => ({
            type: v.violation_type,
            severity: v.severity as 'critical' | 'major' | 'minor',
            description: v.description
          }))
        }
        
        setResult(processingResult)
      } else {
        alert('Recording is not yet processed. Status: ' + recording.status)
      }
      setIsProcessing(false)
    } catch (error: any) {
      console.error('Failed to load results:', error)
      alert('Failed to load results: ' + (error.message || 'Unknown error'))
      setIsProcessing(false)
    }
  }

  // Upload file to backend (using direct upload to avoid CORS)
  const uploadFile = async (file: File) => {
    const fileId = crypto.randomUUID()
    const fileObj: UploadedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      file,
      status: 'uploading',
      progress: 0,
    }

    setFiles((prev) => [...prev, fileObj])

    try {
      // Upload file directly through backend (avoids CORS issues)
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress: 20 } : f
      ))

      const recording = await api.uploadFileDirect(file, (progress) => {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, progress: 20 + (progress * 0.8) } : f
        ))
      })

      // Update file status
      setFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { 
              ...f, 
              status: 'uploaded' as const, 
              progress: 100,
              recordingId: recording.id
            } 
          : f
      ))
      
      // Reload history to show new recording
      await loadHistory()
    } catch (error: any) {
      console.error('Upload error:', error)
      setFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { 
              ...f, 
              status: 'error' as const, 
              error: error.message || 'Upload failed' 
            } 
          : f
      ))
    }
  }

  // Poll for recording status and results
  const pollRecordingStatus = async (recordingId: string, fileId: string) => {
    const maxAttempts = 60 // 5 minutes max (5 second intervals)
    let attempts = 0

    const poll = async () => {
      try {
        const recording = await api.getRecording(recordingId)
        
        if (recording.status === 'completed') {
          // Get evaluation results
          try {
            const evaluation = await api.getEvaluation(recordingId)
            
            // Get transcript with diarized segments
            let transcript = 'Transcript not available'
            let diarizedSegments: Array<{speaker: string, text: string, start: number, end: number}> | null = null
            try {
              const transcriptData = await api.getTranscript(recordingId)
              transcript = transcriptData.transcript_text
              diarizedSegments = transcriptData.diarized_segments || null
            } catch (transcriptError) {
              console.warn('Could not fetch transcript:', transcriptError)
            }
            
            // Transform evaluation data to ProcessingResult format
            const processingResult: ProcessingResult = {
              transcript,
              diarizedSegments,
              overallScore: evaluation.overall_score,
              resolutionDetected: evaluation.resolution_detected,
              resolutionConfidence: evaluation.resolution_confidence,
              customerTone: evaluation.customer_tone ? {
                primary_emotion: evaluation.customer_tone.primary_emotion,
                confidence: evaluation.customer_tone.confidence,
                description: evaluation.customer_tone.description,
                emotional_journey: evaluation.customer_tone.emotional_journey
              } : undefined,
              categoryScores: evaluation.category_scores.map(cs => ({
                category: cs.category_name,
                score: cs.score,
                feedback: cs.feedback || ''
              })),
              violations: evaluation.policy_violations.map(v => ({
                type: v.violation_type,
                severity: v.severity as 'critical' | 'major' | 'minor',
                description: v.description
              }))
            }
            
            setResult(processingResult)
            setIsProcessing(false)
            
            setFiles(prev => prev.map(f => 
              f.id === fileId 
                ? { ...f, status: 'completed' as const }
                : f
            ))
          } catch (evalError: any) {
            // Evaluation might not be ready yet, continue polling
            if (attempts < maxAttempts) {
              setTimeout(poll, 5000)
              attempts++
            } else {
              throw new Error('Evaluation timeout - processing may still be in progress')
            }
          }
        } else if (recording.status === 'failed') {
          throw new Error(recording.error_message || 'Processing failed')
        } else if (recording.status === 'processing' || recording.status === 'queued') {
          // Continue polling
          if (attempts < maxAttempts) {
            setTimeout(poll, 5000)
            attempts++
          } else {
            throw new Error('Processing timeout - please check the recording status later')
          }
        }
      } catch (error: any) {
        console.error('Polling error:', error)
        setIsProcessing(false)
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { 
                ...f, 
                status: 'error' as const, 
                error: error.message || 'Failed to get processing status' 
              } 
            : f
        ))
      }
    }

    // Start polling
    poll()
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      uploadFile(file)
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.flac'],
      'video/*': ['.mp4', '.mov', '.avi'],
    },
    maxSize: 2 * 1024 * 1024 * 1024,
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
    if (selectedFile?.id === id) {
      setSelectedFile(null)
      setResult(null)
    }
  }

  const handleProcess = async (file: UploadedFile) => {
    if (!file.recordingId) {
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { ...f, status: 'error' as const, error: 'No recording ID found' }
          : f
      ))
      return
    }

    setSelectedFile(file)
    setResult(null)
    setIsProcessing(true)
    setFiles(prev => prev.map(f => 
      f.id === file.id 
        ? { ...f, status: 'processing' as const }
        : f
    ))
    
    // Start polling for results
    await pollRecordingStatus(file.recordingId, file.id)
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Enhanced background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Large ambient lights */}
        <div className="absolute top-0 -right-40 w-[750px] h-[750px] bg-brand-400/11 dark:bg-brand-500/5.5 rounded-full blur-[110px]"></div>
        <div className="absolute top-1/2 -left-40 w-[650px] h-[650px] bg-blue-400/9 dark:bg-blue-500/4.5 rounded-full blur-[95px]"></div>
        <div className="absolute bottom-0 right-1/3 w-[600px] h-[600px] bg-purple-400/8 dark:bg-purple-500/4 rounded-full blur-[90px]"></div>
        
        {/* Medium accent lights */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-cyan-400/6 dark:bg-cyan-500/3 rounded-full blur-[80px]"></div>
        <div className="absolute bottom-1/3 left-0 w-96 h-96 bg-emerald-400/5 dark:bg-emerald-500/2.5 rounded-full blur-3xl"></div>
        
        {/* Small highlight lights */}
        <div className="absolute top-1/3 right-1/4 w-64 h-64 bg-indigo-400/4 dark:bg-indigo-500/2 rounded-full blur-2xl"></div>
        
        {/* Gradient overlays for depth */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/10 via-transparent to-purple-50/5 dark:from-blue-900/5 dark:via-transparent dark:to-purple-900/3"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(59,130,246,0.08),transparent_60%)] dark:bg-[radial-gradient(ellipse_at_top_right,rgba(59,130,246,0.04),transparent_60%)]"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Test QA System
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload recordings to test the AI-powered quality assurance flow
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setShowHistory(!showHistory)
              if (!showHistory) {
                loadHistory()
              }
            }}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-2"
          >
            <FaHistory className="w-4 h-4" />
            <span>{showHistory ? 'Hide History' : 'Show History'}</span>
          </button>
          <Link
            to="/policy-templates"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-2"
          >
            <FaCog className="w-4 h-4" />
            <span>Configure Policies</span>
          </Link>
        </div>
      </div>


      {/* Active Template Info */}
      <TemplateInfo />

      {/* Audio Player */}
      {audioUrl && (
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <button
                onClick={toggleAudio}
                className="p-3 bg-brand-500 text-white rounded-full hover:bg-brand-600 flex items-center justify-center"
              >
                {isPlaying ? <FaPause className="w-4 h-4" /> : <FaPlay className="w-4 h-4" />}
              </button>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {history.find(r => r.id === selectedRecordingId)?.file_name || 'Audio File'}
                </p>
                <audio ref={audioRef} controls className="w-full mt-2" style={{ height: '32px' }}>
                  Your browser does not support the audio element.
                </audio>
              </div>
            </div>
            <button
              onClick={() => {
                setAudioUrl(null)
                setSelectedRecordingId(null)
                if (audioRef.current) {
                  audioRef.current.pause()
                  audioRef.current.src = ''
                }
                setIsPlaying(false)
              }}
              className="ml-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <FaTimes className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Recording History */}
      {showHistory && (
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
              <FaHistory className="w-5 h-5" />
              <span>Recording History</span>
            </h2>
            <button
              onClick={loadHistory}
              disabled={loadingHistory}
              className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-2 text-sm disabled:opacity-50"
            >
              <FaSpinner className={`w-4 h-4 ${loadingHistory ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
          {loadingHistory ? (
            <div className="text-center py-8">
              <FaSpinner className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-2" />
              <p className="text-gray-600 dark:text-gray-400">Loading history...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p>No recordings found. Upload a file to get started.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {history.map((recording) => (
                <div
                  key={recording.id}
                  className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <FaFileAudio className="w-5 h-5 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {recording.file_name}
                          </p>
                          <div className="flex items-center space-x-4 mt-1">
                            <span className={`text-xs px-2 py-1 rounded ${
                              recording.status === 'completed' 
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                : recording.status === 'processing' || recording.status === 'queued'
                                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                                : recording.status === 'failed'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                            }`}>
                              {recording.status}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {formatDate(recording.uploaded_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => loadAudioUrl(recording.id)}
                        className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                        title="Listen to audio"
                      >
                        <FaVolumeUp className="w-4 h-4" />
                      </button>
                      {recording.status === 'completed' && (
                        <>
                          <button
                            onClick={() => loadRecordingResults(recording.id)}
                            className="p-2 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                            title="View results"
                          >
                            <FaChartBar className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleReevaluate(recording.id)}
                            className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded"
                            title="Re-evaluate"
                          >
                            <FaRedo className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDeleteRecording(recording.id)}
                        className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        title="Delete recording"
                      >
                        <FaTrash className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Upload */}
        <div className="space-y-6">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
              ${
                isDragActive
                  ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20'
                  : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
              }
            `}
          >
            <input {...getInputProps()} />
            <FaCloudUploadAlt
              className={`mx-auto h-12 w-12 mb-4 ${
                isDragActive
                  ? 'text-brand-500'
                  : 'text-gray-400 dark:text-gray-500'
              }`}
            />
            <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to select'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Supported: MP3, WAV, M4A, MP4 (Max 2GB)
            </p>
          </div>

          {/* Uploaded Files List */}
          {files.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Uploaded Files ({files.length})
              </h2>
              <div className="space-y-3">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <FaFileAudio className="w-5 h-5 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.status === 'uploading' && (
                        <div className="flex items-center space-x-2">
                          <FaSpinner className="w-4 h-4 animate-spin text-brand-500" />
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Uploading... {file.progress}%
                          </span>
                        </div>
                      )}
                      {file.status === 'uploaded' && (
                        <button
                          onClick={() => handleProcess(file)}
                          className="px-3 py-1.5 bg-brand-500 text-white text-sm rounded-lg hover:bg-brand-600 flex items-center space-x-1"
                        >
                          <FaPlay className="w-4 h-4" />
                          <span>Process</span>
                        </button>
                      )}
                      {file.status === 'processing' && (
                        <div className="flex items-center space-x-2 text-brand-600 dark:text-brand-400">
                          <FaSpinner className="w-4 h-4 animate-spin" />
                          <span className="text-sm">Processing...</span>
                        </div>
                      )}
                      {file.status === 'completed' && (
                        <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                          <FaCheckCircle className="w-4 h-4" />
                          <span className="text-sm">Completed</span>
                        </div>
                      )}
                      {file.status === 'error' && (
                        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
                          <FaExclamationCircle className="w-4 h-4" />
                          <span className="text-xs">{file.error}</span>
                        </div>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Results */}
        <div>
          {isProcessing && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
              <FaSpinner className="w-12 h-12 text-brand-500 animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Processing Recording...
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Analyzing audio, transcribing, and evaluating quality
              </p>
            </div>
          )}

          {result && selectedFile && (
            <div className="space-y-6">
              {/* Overall Score */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Results: {selectedFile.name}
                  </h2>
                  <FaChartBar className="w-6 h-6 text-brand-500" />
                </div>
                <div className="text-center py-4">
                  <div className="text-5xl font-bold text-brand-600 dark:text-brand-400 mb-2">
                    {result.overallScore}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Overall Quality Score
                  </div>
                  <div className="flex items-center justify-center space-x-4 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Resolution: </span>
                      <span className={result.resolutionDetected ? 'text-green-600 dark:text-green-400 font-medium' : 'text-red-600 dark:text-red-400 font-medium'}>
                        {result.resolutionDetected ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Confidence: </span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {(result.resolutionConfidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Customer Tone */}
              {result.customerTone && (
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                      <FaUser className="w-5 h-5 text-purple-500" />
                      <span>Customer Tone Analysis</span>
                    </h3>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Primary Emotion:</span>
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            result.customerTone.primary_emotion === 'angry' || result.customerTone.primary_emotion === 'frustrated'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                              : result.customerTone.primary_emotion === 'satisfied' || result.customerTone.primary_emotion === 'happy'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                              : result.customerTone.primary_emotion === 'neutral' || result.customerTone.primary_emotion === 'calm'
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                              : result.customerTone.primary_emotion === 'disappointed' || result.customerTone.primary_emotion === 'confused'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}>
                            {result.customerTone.primary_emotion.charAt(0).toUpperCase() + result.customerTone.primary_emotion.slice(1)}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            ({(result.customerTone.confidence * 100).toFixed(0)}% confidence)
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {result.customerTone.description}
                        </p>
                      </div>
                    </div>
                    
                    {result.customerTone.emotional_journey && result.customerTone.emotional_journey.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Emotional Journey</h4>
                        <div className="space-y-3">
                          {result.customerTone.emotional_journey.map((journey, idx) => (
                            <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
                                  {journey.segment}
                                </span>
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  journey.emotion === 'angry' || journey.emotion === 'frustrated'
                                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                    : journey.emotion === 'satisfied' || journey.emotion === 'happy'
                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                                    : journey.emotion === 'neutral' || journey.emotion === 'calm'
                                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                                }`}>
                                  {journey.emotion}
                                </span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  ({journey.intensity} intensity)
                                </span>
                              </div>
                              <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                                "{journey.evidence}"
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Category Scores */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Category Scores
                </h3>
                <div className="space-y-4">
                  {result.categoryScores.map((category, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {category.category}
                        </span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">
                          {category.score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                        <div
                          className="bg-brand-500 h-2 rounded-full"
                          style={{ width: `${category.score}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {category.feedback}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Violations */}
              {result.violations.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Policy Violations
                  </h3>
                  <div className="space-y-3">
                    {result.violations.map((violation, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-red-900 dark:text-red-200">
                            {violation.type}
                          </span>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              violation.severity === 'critical'
                                ? 'bg-red-600 text-white'
                                : violation.severity === 'major'
                                ? 'bg-orange-600 text-white'
                                : 'bg-yellow-600 text-white'
                            }`}
                          >
                            {violation.severity}
                          </span>
                        </div>
                        <p className="text-sm text-red-700 dark:text-red-300">
                          {violation.description}
                        </p>
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                          Timestamp: {violation.timestamp}s
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Transcript */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Transcript
                </h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                  {result.diarizedSegments && result.diarizedSegments.length > 0 ? (
                    <div className="space-y-3">
                      {result.diarizedSegments.map((segment, index) => {
                        const isCaller = segment.speaker === 'caller'
                        const isAgent = segment.speaker === 'agent' || segment.speaker.startsWith('agent')
                        const speakerLabel = isCaller ? 'Caller' : isAgent ? 'Agent' : segment.speaker
                        
                        return (
                          <div
                            key={index}
                            className={`p-3 rounded-lg ${
                              isCaller
                                ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                                : isAgent
                                ? 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500'
                                : 'bg-gray-100 dark:bg-gray-800 border-l-4 border-gray-400'
                            }`}
                          >
                            <div className="flex items-start justify-between mb-1">
                              <span
                                className={`text-xs font-semibold uppercase ${
                                  isCaller
                                    ? 'text-blue-700 dark:text-blue-300'
                                    : isAgent
                                    ? 'text-green-700 dark:text-green-300'
                                    : 'text-gray-600 dark:text-gray-400'
                                }`}
                              >
                                {speakerLabel}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatTime(segment.start)} - {formatTime(segment.end)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {segment.text}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                      {result.transcript}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          )}

          {!isProcessing && !result && files.length === 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
              <FaChartBar className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No Results Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Upload a file and click "Process" to see QA results here
              </p>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  )
}

// Component to show active template info
function TemplateInfo() {
  const [activeTemplate, setActiveTemplate] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTemplate = async () => {
      try {
        const templates = await api.getTemplates()
        const active = templates.find(t => t.is_active) || null
        setActiveTemplate(active)
      } catch (err) {
        // Silently fail - template info is optional
        console.warn('Could not load templates:', err)
      } finally {
        setLoading(false)
      }
    }
    loadTemplate()
  }, [])

  if (loading || !activeTemplate) return null

  return (
    <div className="mb-6 p-4 bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800 rounded-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-brand-900 dark:text-brand-200">
            Active Policy Template: {activeTemplate.template_name}
          </p>
          <p className="text-xs text-brand-700 dark:text-brand-300 mt-1">
            {activeTemplate.criteria.length} evaluation criteria configured
          </p>
        </div>
        <Link
          to="/policy-templates"
          className="text-sm text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300"
        >
          Edit Template →
        </Link>
      </div>
    </div>
  )
}

