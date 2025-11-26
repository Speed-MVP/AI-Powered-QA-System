import { useState, useEffect } from 'react'
import { FaQuestionCircle, FaTimes, FaSpinner } from 'react-icons/fa'

interface PromptModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (value: string) => void
  title: string
  message: string
  defaultValue?: string
  placeholder?: string
  inputType?: 'text' | 'number' | 'email' | 'password'
  confirmText?: string
  cancelText?: string
  loading?: boolean
  required?: boolean
  validator?: (value: string) => boolean | string
}

export function PromptModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  defaultValue = '',
  placeholder = '',
  inputType = 'text',
  confirmText = 'OK',
  cancelText = 'Cancel',
  loading = false,
  required = false,
  validator,
}: PromptModalProps) {
  const [value, setValue] = useState(defaultValue)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setValue(defaultValue)
      setError(null)
    }
  }, [isOpen, defaultValue])

  const handleConfirm = () => {
    if (required && !value.trim()) {
      setError('This field is required')
      return
    }

    if (validator) {
      const result = validator(value)
      if (result !== true) {
        setError(typeof result === 'string' ? result : 'Invalid value')
        return
      }
    }

    onConfirm(value)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleConfirm()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FaQuestionCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <FaTimes className="w-5 h-5" />
            </button>
          </div>
        </div>
        <div className="p-6 space-y-4">
          {message && (
            <p className="text-sm text-gray-700 dark:text-gray-300">{message}</p>
          )}
          <div>
            <input
              type={inputType}
              value={value}
              onChange={(e) => {
                setValue(e.target.value)
                setError(null)
              }}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className={`w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                error ? 'border-red-300 dark:border-red-600' : 'border-gray-300 dark:border-gray-600'
              }`}
              autoFocus
            />
            {error && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
            )}
          </div>
        </div>
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={loading || (required && !value.trim())}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <FaSpinner className="w-4 h-4 animate-spin" /> : null}
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}


