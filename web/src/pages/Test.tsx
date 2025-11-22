import { useCallback, useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { FaCloudUploadAlt, FaCheckCircle, FaSpinner, FaFileAudio, FaPlay, FaChartBar, FaCog, FaExclamationCircle, FaTrash, FaRedo, FaVolumeUp, FaPause, FaHistory, FaTimes, FaUser, FaInfoCircle } from 'react-icons/fa'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { ConfirmModal } from '@/components/modals'

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
  const [audioError, setAudioError] = useState<string | null>(null)
  const [loadingAudio, setLoadingAudio] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)
  const notificationTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; title: string; message: string; onConfirm: () => void } | null>(null)

  const showNotification = (type: 'success' | 'error' | 'info', message: string, duration = 5000) => {
    if (notificationTimeout.current) {
      clearTimeout(notificationTimeout.current)
      notificationTimeout.current = null
    }
    setNotification({ type, message })
    notificationTimeout.current = setTimeout(() => {
      setNotification(null)
      notificationTimeout.current = null
    }, duration)
  }

  const dismissNotification = () => {
    if (notificationTimeout.current) {
      clearTimeout(notificationTimeout.current)
      notificationTimeout.current = null
    }
    setNotification(null)
  }

  useEffect(() => {
    return () => {
      if (notificationTimeout.current) {
        clearTimeout(notificationTimeout.current)
      }
    }
  }, [])

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

  // Load audio URL for playback and auto-play
  const loadAudioUrl = async (recordingId: string) => {
    try {
      setLoadingAudio(true)
      setAudioError(null)
      const { download_url } = await api.getDownloadUrl(recordingId)
      console.log('Download URL received:', download_url)
      setAudioUrl(download_url)
      setSelectedRecordingId(recordingId)
      // Auto-play will be handled by the canplay event
    } catch (error: any) {
      console.error('Failed to load audio URL:', error)
      setAudioError(error.message || 'Failed to load audio file')
      showNotification('error', 'Failed to load audio file: ' + (error.message || 'Unknown error'))
      setLoadingAudio(false)
    }
  }

  // Sync audio element properties when URL changes
  useEffect(() => {
    const audio = audioRef.current
    if (audio && audioUrl) {
      console.log('Audio URL changed, updating audio element:', audioUrl)
      setLoadingAudio(true)
      setAudioError(null)
      // Ensure audio is not muted and volume is set
      audio.volume = 1.0
      audio.muted = false
      // Note: src will be set via JSX attribute, but we ensure volume here
      // Loading state will be updated by audio event handlers
    } else if (audio && !audioUrl) {
      // Clear audio when URL is removed
      audio.src = ''
      audio.load()
      setLoadingAudio(false)
    }
  }, [audioUrl])

  // Handle audio play/pause
  const toggleAudio = async () => {
    const audio = audioRef.current
    if (!audio || !audioUrl) {
      console.warn('Cannot toggle audio: audio element or URL not available')
      return
    }

    try {
      console.log('Toggle audio called, current state:', {
        isPlaying,
        paused: audio.paused,
        readyState: audio.readyState,
        volume: audio.volume,
        muted: audio.muted,
        src: audio.src
      })

      if (isPlaying || !audio.paused) {
        console.log('Pausing audio')
        audio.pause()
        // State will be updated by pause event listener
      } else {
        console.log('Attempting to play audio')
        // Ensure volume is set and not muted
        audio.volume = 1.0
        audio.muted = false
        
        const playPromise = audio.play()
        
        if (playPromise !== undefined) {
          await playPromise
          console.log('Audio play promise resolved')
        } else {
          console.log('Audio play started (no promise)')
        }
        // State will be updated by play event listener
      }
    } catch (error: any) {
      console.error('Error playing audio:', error)
      let errorMessage = 'Failed to play audio: ' + (error.message || 'Unknown error')
      
      // Handle autoplay policy errors
      if (error.name === 'NotAllowedError' || error.name === 'NotSupportedError') {
        errorMessage = 'Autoplay blocked. Please click the play button to start playback.'
      }
      
      setAudioError(errorMessage)
      setIsPlaying(false)
    }
  }

  // Handle audio events - set up when audio element is available
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      // Audio element not yet in DOM, skip setting up listeners
      // This useEffect will run again when audioUrl changes and element is rendered
      return
    }

    const handlePlay = () => {
      console.log('Audio started playing - play event fired', {
        currentTime: audio.currentTime,
        duration: audio.duration,
        volume: audio.volume,
        muted: audio.muted
      })
      setIsPlaying(true)
      setAudioError(null)
    }
    
    const handlePlaying = () => {
      console.log('Audio is now playing (playing event)')
    }
    
    const handleWaiting = () => {
      console.log('Audio is waiting for data')
    }

    const handlePause = () => {
      console.log('Audio paused')
      setIsPlaying(false)
    }

    const handleEnded = () => {
      console.log('Audio ended')
      setIsPlaying(false)
    }

    const handleError = (e: Event) => {
      console.error('Audio error:', e, audio.error)
      const error = audio.error
      let errorMessage = 'Failed to load audio'
      
      if (error) {
        switch (error.code) {
          case error.MEDIA_ERR_ABORTED:
            errorMessage = 'Audio loading aborted'
            break
          case error.MEDIA_ERR_NETWORK:
            errorMessage = 'Network error while loading audio. Please check your connection or try again.'
            break
          case error.MEDIA_ERR_DECODE:
            errorMessage = 'Audio decoding error. The file may be corrupted.'
            break
          case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
            errorMessage = 'Audio format not supported by your browser'
            break
          default:
            errorMessage = `Unknown audio error (code: ${error.code})`
        }
      }
      
      setAudioError(errorMessage)
      setIsPlaying(false)
      setLoadingAudio(false)
    }

    const handleLoadedData = async () => {
      console.log('Audio data loaded successfully')
      setLoadingAudio(false)
      setAudioError(null)
      
      // Try to auto-play if audio is ready and paused
      if (audio.paused && audioUrl && audio.readyState >= 2) {
        try {
          console.log('Attempting to auto-play after data loaded')
          audio.volume = 1.0
          audio.muted = false
          await audio.play()
          console.log('Audio auto-play successful after data loaded')
        } catch (error: any) {
          console.warn('Auto-play failed after data loaded:', error)
          // Don't show error for autoplay blocks
          if (error.name !== 'NotAllowedError') {
            setAudioError('Could not auto-play. Please click the play button.')
          }
        }
      }
    }

    const handleLoadStart = () => {
      console.log('Audio loading started')
      setLoadingAudio(true)
      setAudioError(null)
    }

    const handleCanPlay = async () => {
      console.log('Audio can start playing', {
        readyState: audio.readyState,
        paused: audio.paused,
        duration: audio.duration,
        volume: audio.volume,
        muted: audio.muted
      })
      setLoadingAudio(false)
      // Ensure volume is set
      audio.volume = 1.0
      audio.muted = false
      
      // Auto-play when audio is ready
      if (audio.paused && audioUrl) {
        try {
          console.log('Attempting to auto-play audio')
          await audio.play()
          console.log('Audio auto-play successful')
        } catch (error: any) {
          console.warn('Auto-play failed (this is normal if browser blocks autoplay):', error)
          // Don't show error for autoplay blocks - user can click play button
          if (error.name !== 'NotAllowedError') {
            setAudioError('Could not auto-play. Please click the play button.')
          }
        }
      }
    }
    
    const handleLoadedMetadata = () => {
      console.log('Audio metadata loaded', {
        duration: audio.duration,
        readyState: audio.readyState
      })
    }

    audio.addEventListener('play', handlePlay)
    audio.addEventListener('playing', handlePlaying)
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)
    audio.addEventListener('loadeddata', handleLoadedData)
    audio.addEventListener('loadstart', handleLoadStart)
    audio.addEventListener('canplay', handleCanPlay)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('waiting', handleWaiting)

    // Set initial volume and unmute
    audio.volume = 1.0
    audio.muted = false
    
    // Log current state
    console.log('Audio element setup complete', {
      src: audio.src,
      volume: audio.volume,
      muted: audio.muted,
      paused: audio.paused,
      readyState: audio.readyState
    })

    return () => {
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('playing', handlePlaying)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
      audio.removeEventListener('loadeddata', handleLoadedData)
      audio.removeEventListener('loadstart', handleLoadStart)
      audio.removeEventListener('canplay', handleCanPlay)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('waiting', handleWaiting)
    }
  }, [audioUrl]) // Re-setup when audioUrl changes to ensure we have the latest audio element

  // Delete recording
  const handleDeleteRecording = async (recordingId: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Recording',
      message: 'Are you sure you want to delete this recording? This will permanently delete the file from storage.',
      onConfirm: async () => {
        setConfirmModal(null)
        try {
          await api.deleteRecording(recordingId)
          setHistory(prev => prev.filter(r => r.id !== recordingId))
          if (selectedRecordingId === recordingId) {
            setSelectedRecordingId(null)
            setAudioUrl(null)
            setResult(null)
          }
          showNotification('success', 'Recording deleted successfully')
        } catch (error: any) {
          console.error('Failed to delete recording:', error)
          showNotification('error', 'Failed to delete recording: ' + (error.message || 'Unknown error'))
        }
      },
    })
  }

  // Reevaluate recording
  const handleReevaluate = async (recordingId: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Re-evaluate Recording',
      message: 'This will re-evaluate the recording. Continue?',
      onConfirm: async () => {
        setConfirmModal(null)
        try {
          await api.reevaluateRecording(recordingId)
          showNotification('info', 'Re-evaluation started. Results will update once processing completes.')
          // Begin polling immediately (don't rely on stale history state)
          setIsProcessing(true)
          setResult(null)
          setSelectedRecordingId(recordingId)
          await loadHistory()
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
                  violations: [] // Phase 7: Violations are now handled through compliance rules in deterministic_results
                }
                
                setResult(processingResult)
                setIsProcessing(false)
                await loadHistory()
              } else if (updated.status === 'failed') {
                showNotification('error', 'Re-evaluation failed: ' + (updated.error_message || 'Unknown error'))
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
        } catch (error: any) {
          console.error('Failed to reevaluate:', error)
          
          // Check for connection errors
          let errorMessage = error.message || 'Unknown error'
          
          if (error.message?.includes('Failed to fetch') || error.message?.includes('network')) {
            errorMessage = 'Cannot connect to backend server. Please make sure the backend is running on http://localhost:8000'
          } else if (error.message?.includes('CORS')) {
            errorMessage = 'CORS error: Backend server may not be running or CORS is not configured correctly.'
          } else if (error.message?.includes('500')) {
            errorMessage = 'Server error: ' + (error.message || 'Internal server error occurred')
          }
          
          showNotification('error', `Failed to start re-evaluation: ${errorMessage}`)
        }
      },
    })
  }

  // Removed: loadRecordingResults (navigation now handled via Link to /results/:recordingId)

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

      const recording = await api.uploadFileDirect(file)
      // Simulate progress to completion after upload succeeds
        setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress: 100 } : f
        ))

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
              violations: [] // Phase 7: Violations are now handled through compliance rules in deterministic_results
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Professional Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <FaChartBar className="w-5 h-5 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Quality Assurance Testing
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Test and validate your QA evaluation system
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                  <span className="font-semibold">Setup Flow:</span> SOP Builder → Compliance Rules → Rubric Builder → Activate
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  setShowHistory(!showHistory)
                  if (!showHistory) {
                    loadHistory()
                  }
                }}
                className="inline-flex items-center px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <FaHistory className="w-4 h-4 mr-2" />
                {showHistory ? 'Hide Records' : 'View Records'}
              </button>
              
              {/* Workflow Steps - Clear Visual Flow */}
              <div className="flex items-center space-x-2 border-l border-slate-300 dark:border-slate-600 pl-4 ml-2">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mr-1">Setup:</span>
                
                {/* Step 1: SOP Builder */}
                <Link
                  to="/sop-builder"
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 relative group"
                  title="Step 1: Define your call flow stages and steps"
                >
                  <span className="absolute -left-2 -top-2 w-5 h-5 bg-blue-800 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 border-white dark:border-slate-800">
                    1
                  </span>
                  <FaCog className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">SOP Builder</span>
                  <span className="sm:hidden">SOP</span>
                </Link>
                
                {/* Arrow */}
                <span className="text-slate-400 dark:text-slate-500 text-xs">→</span>
                
                {/* Step 2: Compliance Rules */}
                <Link
                  to="/compliance-rules"
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 relative group"
                  title="Step 2: Define mandatory compliance rules"
                >
                  <span className="absolute -left-2 -top-2 w-5 h-5 bg-blue-800 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 border-white dark:border-slate-800">
                    2
                  </span>
                  <FaCog className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Compliance Rules</span>
                  <span className="sm:hidden">Rules</span>
                </Link>
                
                {/* Arrow */}
                <span className="text-slate-400 dark:text-slate-500 text-xs">→</span>
                
                {/* Step 3: Rubric Builder */}
                <Link
                  to="/rubric-builder"
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 relative group"
                  title="Step 3: Define scoring categories and mappings"
                >
                  <span className="absolute -left-2 -top-2 w-5 h-5 bg-blue-800 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 border-white dark:border-slate-800">
                    3
                  </span>
                  <FaCog className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Rubric Builder</span>
                  <span className="sm:hidden">Rubric</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {notification && (
          <div
            className={`mb-6 rounded-lg border p-4 shadow-sm flex items-start justify-between space-x-4 ${
              notification.type === 'success'
                ? 'bg-green-50 border-green-200'
                : notification.type === 'error'
                ? 'bg-red-50 border-red-200'
                : 'bg-blue-50 border-blue-200'
            }`}
          >
            <div className="flex items-start space-x-3">
              <div className="mt-1">
                {notification.type === 'success' && <FaCheckCircle className="w-5 h-5 text-green-600" />}
                {notification.type === 'error' && <FaExclamationCircle className="w-5 h-5 text-red-600" />}
                {notification.type === 'info' && <FaInfoCircle className="w-5 h-5 text-blue-600" />}
              </div>
              <p
                className={`text-sm leading-6 ${
                  notification.type === 'success'
                    ? 'text-green-800'
                    : notification.type === 'error'
                    ? 'text-red-800'
                    : 'text-blue-800'
                }`}
              >
                {notification.message}
              </p>
            </div>
            <button
              onClick={dismissNotification}
              className="text-slate-500 hover:text-slate-700 transition-colors"
              aria-label="Dismiss notification"
            >
              <FaTimes className="w-4 h-4" />
            </button>
          </div>
        )}
        {/* Status Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaFileAudio className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <dt className="text-sm font-medium text-slate-600 dark:text-slate-400 truncate">
                  Files Uploaded
                </dt>
                <dd className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {files.length}
                </dd>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaSpinner className={`w-6 h-6 ${isProcessing ? 'text-orange-600 animate-spin' : 'text-green-600'}`} />
              </div>
              <div className="ml-4">
                <dt className="text-sm font-medium text-slate-600 dark:text-slate-400 truncate">
                  Processing Status
                </dt>
                <dd className="text-lg font-semibold text-slate-900 dark:text-white">
                  {isProcessing ? 'Active' : 'Ready'}
                </dd>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaChartBar className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <dt className="text-sm font-medium text-slate-600 dark:text-slate-400 truncate">
                  Evaluations Done
                </dt>
                <dd className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {history.filter(h => h.status === 'completed').length}
                </dd>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaCog className="w-6 h-6 text-slate-600" />
              </div>
              <div className="ml-4">
                <dt className="text-sm font-medium text-slate-600 dark:text-slate-400 truncate">
                  Active Template
                </dt>
                <dd className="text-lg font-semibold text-slate-900 dark:text-white">
                  {/* Legacy PolicyTemplate removed - use FlowVersion + RubricTemplate instead */}
                </dd>
              </div>
            </div>
          </div>
        </div>

        {/* Recording History */}
        {showHistory && (
          <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Test Records
                </h2>
                <button
                  onClick={loadHistory}
                  disabled={loadingHistory}
                  className="inline-flex items-center px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50"
                >
                  <FaSpinner className={`w-4 h-4 mr-2 ${loadingHistory ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>
            <div className="p-6">
              {loadingHistory ? (
                <div className="text-center py-12">
                  <FaSpinner className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
                  <p className="text-slate-600 dark:text-slate-400">Loading records...</p>
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-12">
                  <FaFileAudio className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                    No test records
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Upload and process recordings to see your test history
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((recording) => (
                    <div
                      key={recording.id}
                      className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-3 h-3 rounded-full ${
                          recording.status === 'completed'
                            ? 'bg-green-500'
                            : recording.status === 'processing' || recording.status === 'queued'
                            ? 'bg-orange-500'
                            : recording.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-slate-400'
                        }`}></div>
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {recording.file_name}
                          </p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            {formatDate(recording.uploaded_at)}
                            {recording.duration_seconds && ` • ${formatTime(recording.duration_seconds)}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {recording.status === 'completed' && (
                          <>
                            <button
                              onClick={() => loadAudioUrl(recording.id)}
                              className="inline-flex items-center px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600"
                            >
                              <FaVolumeUp className="w-4 h-4 mr-1" />
                              Listen
                            </button>
                            <Link
                              to={`/results/${recording.id}`}
                              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                            >
                              <FaChartBar className="w-4 h-4 mr-1" />
                              Results
                            </Link>
                            <button
                              onClick={() => handleReevaluate(recording.id)}
                              className="inline-flex items-center px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600"
                            >
                              <FaRedo className="w-4 h-4 mr-1" />
                              Retest
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDeleteRecording(recording.id)}
                          className="inline-flex items-center px-3 py-1.5 border border-red-300 dark:border-red-600 rounded-md text-sm font-medium text-red-700 dark:text-red-200 bg-white dark:bg-slate-700 hover:bg-red-50 dark:hover:bg-red-900/50"
                        >
                          <FaTrash className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Audio Player */}
        {audioUrl && (
          <div className="mb-8 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Audio Playback
              </h3>
            </div>
            <div className="p-6">
              <div className="flex items-center space-x-4">
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    console.log('Play button clicked')
                    toggleAudio()
                  }}
                  disabled={loadingAudio || !!audioError}
                  className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full hover:bg-blue-700 flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                >
                  {loadingAudio ? (
                    <FaSpinner className="w-5 h-5 animate-spin" />
                  ) : isPlaying ? (
                    <FaPause className="w-5 h-5" />
                  ) : (
                    <FaPlay className="w-5 h-5" />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 dark:text-white mb-2">
                    {history.find(r => r.id === selectedRecordingId)?.file_name || 'Audio File'}
                  </p>
                  {audioError && (
                    <div className="mb-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
                      {audioError}
                    </div>
                  )}
                  {loadingAudio && !audioError && (
                    <div className="mb-2 text-sm text-slate-600 dark:text-slate-400">
                      Loading audio...
                    </div>
                  )}
                  <div className="mb-2">
                    <audio 
                      ref={audioRef} 
                      controls 
                      className="w-full"
                      preload="auto"
                      src={audioUrl || undefined}
                      onPlay={(e) => {
                        console.log('Native controls play clicked')
                        const audio = e.currentTarget
                        console.log('Audio state on native play:', {
                          paused: audio.paused,
                          volume: audio.volume,
                          muted: audio.muted,
                          currentTime: audio.currentTime,
                          src: audio.src
                        })
                      }}
                      onPause={() => {
                        console.log('Native controls pause clicked')
                      }}
                    >
                    Your browser does not support the audio element.
                  </audio>
                  </div>
                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 space-x-2 flex flex-wrap gap-2">
                    {audioRef.current ? (
                      <>
                        <span>Volume: {Math.round((audioRef.current.volume || 0) * 100)}%</span>
                        <span>•</span>
                        <span>Muted: {audioRef.current.muted ? 'Yes' : 'No'}</span>
                        <span>•</span>
                        <span>State: {audioRef.current.paused ? 'Paused' : 'Playing'}</span>
                        <span>•</span>
                        <span>Ready: {audioRef.current.readyState >= 2 ? 'Yes' : 'No'}</span>
                        {audioRef.current.duration && (
                          <>
                            <span>•</span>
                            <span>Duration: {formatTime(audioRef.current.duration)}</span>
                          </>
                        )}
                      </>
                    ) : (
                      <span>Audio element not available</span>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    💡 Tip: You can also use the native audio controls above, or click the blue play button
                  </div>
                </div>
                <button
                  onClick={() => {
                    setAudioUrl(null)
                    setSelectedRecordingId(null)
                    setAudioError(null)
                    setLoadingAudio(false)
                    if (audioRef.current) {
                      audioRef.current.pause()
                      audioRef.current.src = ''
                    }
                    setIsPlaying(false)
                  }}
                  className="flex-shrink-0 p-2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                >
                  <FaTimes className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Left Column - Upload */}
          <div className="xl:col-span-1">
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Upload Test Files
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  Upload audio/video files for quality analysis
                </p>
              </div>
              <div className="p-6">
                <div
                  {...getRootProps()}
                  className={`
                    border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                    ${
                      isDragActive
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
                    }
                  `}
                >
                  <input {...getInputProps()} />
                  <FaCloudUploadAlt
                    className={`mx-auto h-10 w-10 mb-3 ${
                      isDragActive
                        ? 'text-blue-500'
                        : 'text-slate-400 dark:text-slate-500'
                    }`}
                  />
                  <p className="text-base font-medium text-slate-900 dark:text-white mb-1">
                    {isDragActive ? 'Drop files here' : 'Upload Files'}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    MP3, WAV, M4A, MP4 up to 2GB each
                  </p>
                </div>

                {/* File Queue */}
                {files.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-sm font-medium text-slate-900 dark:text-white mb-3">
                      File Queue ({files.length})
                    </h3>
                    <div className="space-y-3">
                      {files.map((file) => (
                        <div
                          key={file.id}
                          className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
                        >
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <FaFileAudio className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                                {file.name}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">
                                {formatFileSize(file.size)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {file.status === 'uploading' && (
                              <div className="flex items-center space-x-2">
                                <FaSpinner className="w-4 h-4 animate-spin text-blue-600" />
                                <span className="text-sm text-slate-600 dark:text-slate-400">
                                  {file.progress}%
                                </span>
                              </div>
                            )}
                            {file.status === 'uploaded' && (
                              <button
                                onClick={() => handleProcess(file)}
                                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center space-x-1"
                              >
                                <FaPlay className="w-3 h-3" />
                                <span>Process</span>
                              </button>
                            )}
                            {file.status === 'processing' && (
                              <div className="flex items-center space-x-2 text-orange-600 dark:text-orange-400">
                                <FaSpinner className="w-4 h-4 animate-spin" />
                                <span className="text-sm">Processing</span>
                              </div>
                            )}
                            {file.status === 'completed' && (
                              <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                                <FaCheckCircle className="w-4 h-4" />
                                <span className="text-sm">Done</span>
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
                              className="p-1.5 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                            >
                              <FaTimes className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="xl:col-span-2">
            {isProcessing && (
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8">
                <div className="text-center">
                  <div className="mx-auto flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/50 rounded-full mb-4">
                    <FaSpinner className="w-8 h-8 text-blue-600 animate-spin" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                    Analyzing Recording
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-4">
                    Processing audio, transcribing content, and evaluating quality metrics
                  </p>
                  <div className="flex justify-center space-x-8 text-sm text-slate-500 dark:text-slate-400">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Audio Processing</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-slate-300 rounded-full"></div>
                      <span>Transcription</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-slate-300 rounded-full"></div>
                      <span>Quality Analysis</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Overall Score Card */}
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between">
                      <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                        Analysis Results
                      </h2>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {history.find(r => r.id === selectedRecordingId)?.file_name || selectedFile?.name || 'Recording'}
                        </span>
                        <FaChartBar className="w-5 h-5 text-blue-600" />
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="text-center">
                      <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full mb-4">
                        <span className="text-2xl font-bold text-white">
                          {result.overallScore}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">
                        Quality Score
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400 mb-4">
                        Overall performance assessment
                      </p>
                      <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
                        <div className="text-center">
                          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            result.resolutionDetected
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                          }`}>
                            {result.resolutionDetected ? 'Resolved' : 'Unresolved'}
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Issue Status</p>
                        </div>
                        <div className="text-center">
                          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                            {(result.resolutionConfidence * 100).toFixed(0)}% Confidence
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Resolution Confidence</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Customer Analysis */}
                {result.customerTone && (
                  <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
                        <FaUser className="w-5 h-5 text-purple-600" />
                        <span>Customer Analysis</span>
                      </h3>
                    </div>
                    <div className="p-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <div className="flex items-center space-x-3 mb-3">
                            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                              Primary Emotion
                            </span>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              result.customerTone.primary_emotion === 'angry' || result.customerTone.primary_emotion === 'frustrated'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                : result.customerTone.primary_emotion === 'satisfied' || result.customerTone.primary_emotion === 'happy'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                : result.customerTone.primary_emotion === 'neutral' || result.customerTone.primary_emotion === 'calm'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                                : result.customerTone.primary_emotion === 'disappointed' || result.customerTone.primary_emotion === 'confused'
                                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                                : 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                            }`}>
                              {result.customerTone.primary_emotion.charAt(0).toUpperCase() + result.customerTone.primary_emotion.slice(1)}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                            {result.customerTone.description}
                          </p>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            Analysis Confidence: {(result.customerTone.confidence * 100).toFixed(0)}%
                          </div>
                        </div>

                        {result.customerTone.emotional_journey && result.customerTone.emotional_journey.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                              Call Journey
                            </h4>
                            <div className="space-y-2">
                              {result.customerTone.emotional_journey.map((journey, idx) => (
                                <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-700/50 rounded border border-slate-200 dark:border-slate-600">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase">
                                      {journey.segment}
                                    </span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${
                                      journey.emotion === 'angry' || journey.emotion === 'frustrated'
                                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                        : journey.emotion === 'satisfied' || journey.emotion === 'happy'
                                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                                        : journey.emotion === 'neutral' || journey.emotion === 'calm'
                                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                        : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                                    }`}>
                                      {journey.emotion}
                                    </span>
                                  </div>
                                  <span className="text-xs text-slate-500 dark:text-slate-400">
                                    {journey.intensity}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Category Performance */}
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Category Performance
                    </h3>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4">
                      {result.categoryScores.map((category, idx) => (
                        <div key={idx} className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-medium text-slate-900 dark:text-white">
                              {category.category}
                            </span>
                            <div className="flex items-center space-x-2">
                              <span className="text-lg font-bold text-slate-900 dark:text-white">
                                {category.score}
                              </span>
                              <span className="text-sm text-slate-600 dark:text-slate-400">/100</span>
                            </div>
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-3">
                            <div
                              className={`h-2 rounded-full transition-all ${
                                category.score >= 90 ? 'bg-green-500' :
                                category.score >= 70 ? 'bg-blue-500' :
                                category.score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${category.score}%` }}
                            />
                          </div>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            {category.feedback}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Issues Found */}
                {result.violations.length > 0 && (
                  <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
                        <FaExclamationCircle className="w-5 h-5 text-red-600" />
                        <span>Issues Identified</span>
                      </h3>
                    </div>
                    <div className="p-6">
                      <div className="space-y-3">
                        {result.violations.map((violation, idx) => (
                          <div
                            key={idx}
                            className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-red-900 dark:text-red-200">
                                  {violation.type}
                                </span>
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                    violation.severity === 'critical'
                                      ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200'
                                      : violation.severity === 'major'
                                      ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200'
                                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200'
                                  }`}
                                >
                                  {violation.severity}
                                </span>
                              </div>
                            </div>
                            <p className="text-sm text-red-700 dark:text-red-300 mb-2">
                              {violation.description}
                            </p>
                            {violation.timestamp && (
                              <p className="text-xs text-red-600 dark:text-red-400">
                                Time: {formatTime(violation.timestamp)}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Conversation Transcript */}
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Conversation Transcript
                    </h3>
                  </div>
                  <div className="p-6">
                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                      {result.diarizedSegments && result.diarizedSegments.length > 0 ? (
                        <div className="space-y-4">
                          {result.diarizedSegments.map((segment, index) => {
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
                                    ? 'bg-slate-100 dark:bg-slate-700/50 border-slate-500'
                                    : 'bg-slate-100 dark:bg-slate-700/50 border-slate-400'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span
                                    className={`text-xs font-semibold uppercase tracking-wider ${
                                      isCaller
                                        ? 'text-blue-700 dark:text-blue-300'
                                        : isAgent
                                        ? 'text-slate-700 dark:text-slate-300'
                                        : 'text-slate-600 dark:text-slate-400'
                                    }`}
                                  >
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
                          {result.transcript}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
            </div>
          )}

            {!isProcessing && !result && files.length === 0 && (
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center">
                <div className="mx-auto flex items-center justify-center w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full mb-4">
                  <FaChartBar className="w-8 h-8 text-slate-400 dark:text-slate-500" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  Ready for Testing
                </h3>
                <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                  Upload audio or video files to begin quality assurance testing and evaluation
                </p>
              </div>
            )}
          </div>
        </div>
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
    </div>
  )
}

// Legacy TemplateInfo component removed - PolicyTemplate system no longer exists

