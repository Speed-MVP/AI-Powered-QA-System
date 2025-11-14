import { useEffect, useMemo, useState } from 'react'
import type { Team } from '@/lib/api'

interface AgentFormModalProps {
  open: boolean
  mode: 'create' | 'edit'
  teams: Team[]
  initialData?: {
    full_name: string
    email: string
    team_id?: string | null
  }
  onClose: () => void
  onSave: (payload: { full_name: string; email: string; team_id?: string | null }) => Promise<void>
}

export function AgentFormModal({
  open,
  mode,
  teams,
  initialData,
  onClose,
  onSave,
}: AgentFormModalProps) {
  const [fullName, setFullName] = useState(initialData?.full_name ?? '')
  const [email, setEmail] = useState(initialData?.email ?? '')
  const [teamId, setTeamId] = useState<string | ''>(initialData?.team_id ?? '')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const sortedTeams = useMemo(
    () => [...teams].sort((a, b) => a.name.localeCompare(b.name)),
    [teams],
  )

  useEffect(() => {
    if (open) {
      setFullName(initialData?.full_name ?? '')
      setEmail(initialData?.email ?? '')
      setTeamId(initialData?.team_id ?? '')
      setError(null)
      setIsSubmitting(false)
    }
  }, [open, initialData])

  if (!open) return null

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!fullName.trim()) {
      setError('Full name is required')
      return
    }
    if (!email.trim()) {
      setError('Email is required')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)
      await onSave({
        full_name: fullName.trim(),
        email: email.trim(),
        team_id: teamId || null,
      })
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to save agent')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {mode === 'create' ? 'Add Agent' : 'Edit Agent'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Full name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
              placeholder="e.g. Jordan Smith"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
              placeholder="agent@company.com"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Team
            </label>
            <select
              value={teamId}
              onChange={(event) => setTeamId(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
              disabled={isSubmitting}
            >
              <option value="">Unassigned</option>
              {sortedTeams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-sm text-red-500" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
