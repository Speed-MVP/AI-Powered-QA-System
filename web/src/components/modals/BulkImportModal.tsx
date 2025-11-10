import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { ImportJob } from '@/lib/api'

type Step = 0 | 1 | 2

const SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xlsm']

interface BulkImportModalProps {
  open: boolean
  onClose: () => void
  onComplete?: () => void
}

export function BulkImportModal({ open, onClose, onComplete }: BulkImportModalProps) {
  const [step, setStep] = useState<Step>(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [job, setJob] = useState<ImportJob | null>(null)
  const [polling, setPolling] = useState(false)

  useEffect(() => {
    if (open) {
      setStep(0)
      setSelectedFile(null)
      setError(null)
      setIsUploading(false)
      setJob(null)
      setPolling(false)
    }
  }, [open])

  const handleFileChange = (file: File) => {
    const suffix = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!SUPPORTED_EXTENSIONS.includes(`.${suffix}`)) {
      setError('Unsupported file type. Please upload .csv or .xlsx files.')
      return
    }
    setSelectedFile(file)
    setError(null)
    setStep(1)
  }

  const handleStartImport = async () => {
    if (!selectedFile) {
      setError('Please select a file first.')
      return
    }
    try {
      setIsUploading(true)
      setError(null)
      const createdJob = await api.uploadAgentImport(selectedFile)
      setJob(createdJob)
      setPolling(true)
      setStep(2)
    } catch (err: any) {
      setError(err.message || 'Failed to start import')
    } finally {
      setIsUploading(false)
    }
  }

  useEffect(() => {
    if (!polling || !job?.id) return
    let isActive = true
    const interval = setInterval(async () => {
      try {
        const status = await api.getImportJob(job.id)
        if (!isActive) return
        setJob(status)
        if (status.status !== 'pending' && status.status !== 'processing') {
          clearInterval(interval)
          setPolling(false)
          if (status.status === 'completed' && onComplete) {
            onComplete()
          }
        }
      } catch (err: any) {
        console.error('Failed to poll import job:', err)
        clearInterval(interval)
        setPolling(false)
        setError(err.message || 'Failed to poll import job status')
      }
    }, 2000)
    return () => {
      isActive = false
      clearInterval(interval)
    }
  }, [polling, job?.id, onComplete])

  if (!open) return null

  const stepTitles = ['Upload file', 'Review & confirm', 'Import progress']

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-800">
          <div>
            <p className="text-sm uppercase tracking-wide text-brand-600">Bulk Import</p>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">wUpload agent roster</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="flex border-b border-gray-100 px-6 py-3 text-sm font-medium dark:border-gray-800">
          {stepTitles.map((title, index) => (
            <div
              key={title}
              className={`flex flex-1 items-center ${
                index < step ? 'text-brand-600' : index === step ? 'text-gray-900 dark:text-white' : 'text-gray-400'
              }`}
            >
              <div
                className={`mr-2 flex h-6 w-6 items-center justify-center rounded-full border text-xs ${
                  index < step
                    ? 'border-brand-500 bg-brand-500 text-white'
                    : index === step
                      ? 'border-brand-500 text-brand-500'
                      : 'border-gray-300 text-gray-400'
                }`}
              >
                {index + 1}
              </div>
              <span>{title}</span>
            </div>
          ))}
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-6">
          {step === 0 && (
            <div className="space-y-6">
              <div className="space-y-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Select a CSV or Excel file (.csv, .xlsx, .xlsm). The backend will validate the required columns (
                  <strong>agent_name</strong>, <strong>email</strong>, <strong>team_name</strong>), map them automatically,
                  and create each team/agent as needed.
                </p>
                <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-300 p-8 text-center transition hover:border-brand-500 dark:border-gray-700">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xlsm"
                    className="hidden"
                    onChange={(event) => {
                      const file = event.target.files?.[0]
                      if (file) handleFileChange(file)
                    }}
                  />
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">
                    Click or drag a file to upload
                  </span>
                  {selectedFile && (
                    <p className="mt-2 text-sm text-gray-500">{selectedFile.name}</p>
                  )}
                </label>
              </div>

              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Sample Format</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    Your file should follow this format. Column headers can be in any case (e.g., "Agent Name", "AGENT_NAME", "agent_name").
                  </p>
                </div>
                <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900/50">
                      <tr>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-gray-700 dark:text-gray-300">
                          agent_name
                        </th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-gray-700 dark:text-gray-300">
                          email
                        </th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-gray-700 dark:text-gray-300">
                          team_name
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800 bg-white dark:bg-gray-800">
                      <tr>
                        <td className="px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100">John Doe</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">john.doe@example.com</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">Sales Team</td>
                      </tr>
                      <tr className="bg-gray-50/50 dark:bg-gray-900/30">
                        <td className="px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100">Jane Smith</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">jane.smith@example.com</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">Support Team</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100">Bob Johnson</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">bob.johnson@example.com</td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300">Sales Team</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  <strong>Note:</strong> All three columns are required. Teams will be created automatically if they don't exist.
                </p>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Confirm file</h3>
                <p className="text-sm text-gray-500">
                  Server-side validation will discover discrepancies. You can keep the current file or choose another.
                </p>
              </div>
              <div className="rounded-2xl border border-gray-100 p-4 dark:border-gray-800">
                <p className="text-sm text-gray-600">
                  File: <strong>{selectedFile?.name ?? '—'}</strong>
                </p>
                <p className="text-sm text-gray-600">
                  Size:{' '}
                  <strong>
                    {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : '—'}
                  </strong>
                </p>
                <p className="text-xs text-gray-500">
                  Backend will parse the sheet, normalize headers, and show any validation problems in the job status.
                </p>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Import progress</h3>
                  <p className="text-sm text-gray-500">Polling job status every 2 seconds until it completes.</p>
                </div>
                {job && (
                  <div className="text-right text-sm text-gray-600 dark:text-gray-300">
                    Job ID: <span className="font-mono">{job.id}</span>
                  </div>
                )}
              </div>
              {job ? (
                <div className="rounded-2xl border border-gray-100 p-4 dark:border-gray-800">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">Status</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{job.status}</p>
                  </div>
                  {job.rows_total != null && (
                    <p className="text-sm text-gray-600">
                      Progress: {job.rows_processed ?? 0}/{job.rows_total}
                    </p>
                  )}
                  {job.validation_errors && job.validation_errors.length > 0 && (
                    <div className="mt-4 rounded-xl bg-red-50 p-3 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-200">
                      <p className="font-semibold">Validation issues detected</p>
                      <p>{job.validation_errors.length} error(s) recorded. Download the report from the backend for details.</p>
                    </div>
                  )}
                  {job.status === 'completed' && (
                    <div className="mt-3 rounded-xl bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-200">
                      Import finished: {job.rows_processed ?? 0} succeeded, {job.rows_failed ?? 0} failed.
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-600">Waiting for the import job to start...</p>
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-200">
              {error}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-gray-100 px-6 py-4 dark:border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Close
          </button>
          <div className="space-x-3">
            {step === 0 && (
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={!selectedFile}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
              >
                Continue
              </button>
            )}
            {step === 1 && (
              <button
                type="button"
                onClick={handleStartImport}
                disabled={isUploading}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
              >
                {isUploading ? 'Uploading…' : 'Start import'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
