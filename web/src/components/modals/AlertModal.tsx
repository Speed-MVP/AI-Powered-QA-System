import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimes, FaSpinner } from 'react-icons/fa'

interface AlertModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  message: string
  type?: 'success' | 'error' | 'info' | 'warning'
  buttonText?: string
}

export function AlertModal({
  isOpen,
  onClose,
  title,
  message,
  type = 'info',
  buttonText = 'OK',
}: AlertModalProps) {
  if (!isOpen) return null

  const iconMap = {
    success: { icon: FaCheckCircle, color: 'text-green-600 dark:text-green-400' },
    error: { icon: FaExclamationCircle, color: 'text-red-600 dark:text-red-400' },
    info: { icon: FaInfoCircle, color: 'text-blue-600 dark:text-blue-400' },
    warning: { icon: FaExclamationCircle, color: 'text-orange-600 dark:text-orange-400' },
  }

  const bgColorMap = {
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    error: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    warning: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
  }

  const Icon = iconMap[type].icon
  const iconColor = iconMap[type].color
  const bgColor = bgColorMap[type]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className={`w-5 h-5 ${iconColor}`} />
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
        <div className="p-6">
          <div className={`p-4 rounded-md border ${bgColor}`}>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{message}</p>
          </div>
        </div>
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {buttonText}
          </button>
        </div>
      </div>
    </div>
  )
}


