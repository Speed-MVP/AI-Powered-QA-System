import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { supabase } from '@/lib/supabase'
import { FaCloudUploadAlt, FaCheckCircle, FaExclamationCircle, FaSpinner, FaFileAudio } from 'react-icons/fa'

interface UploadedFile {
  id: string
  name: string
  size: number
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  recordingId?: string
}

export function Upload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const uploadFile = async (file: File) => {
    const fileId = crypto.randomUUID()
    const fileObj: UploadedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0,
    }

    setFiles((prev) => [...prev, fileObj])

    try {
      // Create a unique path for the file
      const timestamp = Date.now()
      const filePath = `${timestamp}_${file.name}`

      // Upload to Supabase Storage
      // Note: Make sure the 'recordings' storage bucket exists in your Supabase project
      const { error: uploadError } = await supabase.storage
        .from('recordings')
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false,
        })

      if (uploadError) {
        // Provide helpful error messages
        if (uploadError.message?.includes('Bucket not found') || uploadError.message?.includes('not found')) {
          throw new Error(
            'Storage bucket "recordings" not found. Please create it in your Supabase Storage settings.'
          )
        }
        throw uploadError
      }

      // Get public URL
      const { data: { publicUrl } } = supabase.storage
        .from('recordings')
        .getPublicUrl(filePath)

      // Create recording record in database
      // For now, we'll use a temporary company_id - this will be replaced with actual auth later
      // Note: Make sure the 'recordings' table exists in your Supabase database
      const { data: recordingData, error: dbError } = await supabase
        .from('recordings')
        .insert({
          file_name: file.name,
          file_url: publicUrl,
          status: 'queued',
          // These will be replaced with actual values when auth is implemented
          company_id: '00000000-0000-0000-0000-000000000000', // Temporary
          uploaded_by_user_id: '00000000-0000-0000-0000-000000000000', // Temporary
        })
        .select()
        .single()

      if (dbError) {
        // If table doesn't exist, provide helpful error message
        if (dbError.code === '42P01' || dbError.message?.includes('does not exist')) {
          throw new Error(
            'Recordings table not found. Please run database migrations first. See DEVELOPMENT.md for setup instructions.'
          )
        }
        throw dbError
      }

      // Update file status to success
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: 'success',
                progress: 100,
                recordingId: recordingData.id,
              }
            : f
        )
      )

      // Trigger processing (if Edge Function is set up)
      // await supabase.functions.invoke('process-recording', {
      //   body: { recording_id: recordingData.id },
      // })
    } catch (error: any) {
      console.error('Upload error:', error)
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: 'error',
                error: error.message || 'Upload failed',
              }
            : f
        )
      )
    }
  }

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => {
        uploadFile(file)
      })
    },
    []
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.flac'],
      'video/*': ['.mp4', '.mov', '.avi'],
    },
    maxSize: 2 * 1024 * 1024 * 1024, // 2GB
    onDragEnter: () => setIsDragging(true),
    onDragLeave: () => setIsDragging(false),
    onDropAccepted: () => setIsDragging(false),
    onDropRejected: () => setIsDragging(false),
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  return (
    <div className="min-h-screen relative">
      {/* Subtle background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-brand-400/8 dark:bg-brand-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 right-0 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-purple-400/8 dark:bg-purple-500/3 rounded-full blur-3xl"></div>
      </div>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Upload Recordings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload audio or video files for AI-powered quality assurance analysis
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          ${
            isDragActive || isDragging
              ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20'
              : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
          }
        `}
      >
        <input {...getInputProps()} />
        <FaCloudUploadAlt
          className={`mx-auto h-12 w-12 mb-4 ${
            isDragActive || isDragging
              ? 'text-brand-500'
              : 'text-gray-400 dark:text-gray-500'
          }`}
        />
        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {isDragActive || isDragging
            ? 'Drop files here'
            : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Supported formats: MP3, WAV, M4A, MP4, MOV, AVI (Max 2GB per file)
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Uploaded Files ({files.length})
          </h2>
          <div className="space-y-3">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1 min-w-0">
                    <FaFileAudio className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatFileSize(file.size)}
                      </p>
                      {file.status === 'uploading' && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-brand-500 h-2 rounded-full"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      {file.status === 'error' && file.error && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                          {file.error}
                        </p>
                      )}
                      {file.status === 'success' && file.recordingId && (
                        <p className="text-xs text-brand-600 dark:text-brand-400 mt-1">
                          Recording ID: {file.recordingId}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {file.status === 'uploading' && (
                      <FaSpinner className="w-5 h-5 text-brand-500 animate-spin" />
                    )}
                    {file.status === 'success' && (
                      <FaCheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {file.status === 'error' && (
                      <>
                        <FaExclamationCircle className="w-5 h-5 text-red-500" />
                        <button
                          onClick={() => removeFile(file.id)}
                          className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                          Remove
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      </div>
    </div>
  )
}

