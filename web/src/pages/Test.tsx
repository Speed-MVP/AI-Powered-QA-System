import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { FaCloudUploadAlt, FaCheckCircle, FaSpinner, FaFileAudio, FaPlay, FaChartBar, FaCog } from 'react-icons/fa'
import { usePolicyStore } from '@/store/policyStore'
import { Link } from 'react-router-dom'

interface UploadedFile {
  id: string
  name: string
  size: number
  file: File
  status: 'uploaded' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
}

interface ProcessingResult {
  transcript: string
  overallScore: number
  resolutionDetected: boolean
  resolutionConfidence: number
  categoryScores: {
    category: string
    score: number
    feedback: string
  }[]
  violations: {
    type: string
    severity: 'critical' | 'major' | 'minor'
    description: string
    timestamp: number
  }[]
}

export function Test() {
  const { activeTemplate } = usePolicyStore()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const simulateProcessing = async (file: UploadedFile) => {
    setIsProcessing(true)
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Use active template criteria or default
    const criteria = activeTemplate?.criteria || []
    
    // Generate mock results based on template criteria
    const categoryScores = criteria.map((criterion) => {
      // Mock score based on category
      const baseScore = Math.floor(Math.random() * 30) + 70 // 70-100
      return {
        category: criterion.categoryName,
        score: baseScore,
        feedback: `Evaluation based on: ${criterion.evaluationPrompt.substring(0, 100)}...`
      }
    })
    
    // Calculate weighted overall score
    const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0)
    const weightedScore = categoryScores.reduce((sum, cs) => {
      const criterion = criteria.find(c => c.categoryName === cs.category)
      return sum + (cs.score * (criterion?.weight || 0) / 100)
    }, 0)
    const overallScore = totalWeight > 0 ? Math.round(weightedScore) : 87
    
    // Mock processing result
    const mockResult: ProcessingResult = {
      transcript: `[Agent] Hello, thank you for calling. How can I assist you today?
[Customer] Hi, I'm having an issue with my account.
[Agent] I'd be happy to help you with that. Can you provide me with your account number?
[Customer] Sure, it's 123456789.
[Agent] Thank you. I can see your account here. What seems to be the issue?
[Customer] I noticed a charge I don't recognize.
[Agent] I understand your concern. Let me review your recent transactions... I can see that charge was for your monthly subscription. Does that help clarify?
[Customer] Oh yes, that makes sense. Thank you!
[Agent] You're welcome! Is there anything else I can help you with today?
[Customer] No, that's all. Thanks again!
[Agent] My pleasure. Have a great day!`,
      overallScore,
      resolutionDetected: true,
      resolutionConfidence: 0.92,
      categoryScores: categoryScores.length > 0 ? categoryScores : [
        {
          category: 'Compliance',
          score: 95,
          feedback: 'Agent followed all compliance guidelines and properly verified customer identity.'
        },
        {
          category: 'Empathy',
          score: 88,
          feedback: 'Agent showed understanding and used appropriate empathetic language.'
        },
        {
          category: 'Resolution',
          score: 92,
          feedback: 'Issue was resolved successfully with customer confirmation.'
        }
      ],
      violations: [
        {
          type: 'Script Adherence',
          severity: 'minor',
          description: 'Agent slightly deviated from greeting script',
          timestamp: 5.2
        }
      ]
    }
    
    setResult(mockResult)
    setIsProcessing(false)
    
    // Update file status
    setFiles(prev => prev.map(f => 
      f.id === file.id 
        ? { ...f, status: 'completed' as const }
        : f
    ))
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const fileObj: UploadedFile = {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        file,
        status: 'uploaded',
        progress: 100,
      }
      setFiles((prev) => [...prev, fileObj])
    })
  }, [])

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
    setSelectedFile(file)
    setResult(null)
    setFiles(prev => prev.map(f => 
      f.id === file.id 
        ? { ...f, status: 'processing' as const }
        : f
    ))
    await simulateProcessing(file)
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
        <Link
          to="/policy-templates"
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center space-x-2"
        >
          <FaCog className="w-4 h-4" />
          <span>Configure Policies</span>
        </Link>
      </div>

      {/* Active Template Info */}
      {activeTemplate && (
        <div className="mb-6 p-4 bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-brand-900 dark:text-brand-200">
                Active Policy Template: {activeTemplate.name}
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
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 max-h-64 overflow-y-auto">
                  <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                    {result.transcript}
                  </pre>
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

