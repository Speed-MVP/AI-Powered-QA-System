import { FaExclamationCircle, FaTimes, FaSpinner } from 'react-icons/fa'

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmColor?: 'red' | 'blue' | 'green' | 'orange'
  loading?: boolean
  danger?: boolean
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmColor = 'blue',
  loading = false,
  danger = false,
}: ConfirmModalProps) {
  if (!isOpen) return null

  const colorClasses = {
    red: 'bg-red-600 hover:bg-red-700',
    blue: 'bg-blue-600 hover:bg-blue-700',
    green: 'bg-green-600 hover:bg-green-700',
    orange: 'bg-orange-600 hover:bg-orange-700',
  }

  const iconColor = danger ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <FaExclamationCircle className={`w-5 h-5 ${iconColor}`} />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
          </div>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{message}</p>
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
            onClick={onConfirm}
            disabled={loading}
            className={`px-4 py-2 text-sm text-white rounded-md disabled:opacity-50 flex items-center gap-2 ${colorClasses[confirmColor]}`}
          >
            {loading ? <FaSpinner className="w-4 h-4 animate-spin" /> : null}
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}


