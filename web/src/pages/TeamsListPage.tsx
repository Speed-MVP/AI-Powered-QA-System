import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { Agent, Team } from '@/lib/api'
import { TeamFormModal } from '@/components/modals/TeamFormModal'

export function TeamsListPage() {
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [teamModal, setTeamModal] = useState<{ open: boolean; mode: 'create' | 'edit'; team?: Team }>({
    open: false,
    mode: 'create',
  })

  const loadDirectory = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [teamData, agentData] = await Promise.all([api.listTeams(), api.listAgents()])
      setTeams(teamData)
      setAgents(agentData)
    } catch (err: any) {
      setError(err.message || 'Failed to load team directory')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDirectory()
  }, [])

  const agentCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    agents.forEach((agent) => {
      agent.team_memberships.forEach((membership) => {
        counts[membership.team_id] = (counts[membership.team_id] || 0) + 1
      })
    })
    return counts
  }, [agents])

  const handleSaveTeam = async (name: string) => {
    if (teamModal.mode === 'edit' && teamModal.team) {
      await api.updateTeam(teamModal.team.id, { name })
    } else {
      await api.createTeam({ name })
    }
    await loadDirectory()
  }

  const handleDeleteTeam = async (team: Team) => {
    const hasAgents = agentCounts[team.id] && agentCounts[team.id] > 0
    const confirmationMessage = hasAgents
      ? `Team "${team.name}" still has assigned agents. Deleting it will remove access from their dashboards. Continue?`
      : `Delete team "${team.name}"?`

    if (!window.confirm(confirmationMessage)) {
      return
    }

    await api.deleteTeam(team.id)
    await loadDirectory()
  }

  const formatDate = (value?: string) => {
    if (!value) return '—'
    return new Date(value).toLocaleDateString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-400/8 dark:bg-brand-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/3 left-0 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/8 dark:bg-purple-500/3 rounded-full blur-3xl"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 relative">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-brand-600">Teams</p>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agent Teams Directory</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Create and manage teams. Import agents from the Agents page.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() =>
                setTeamModal({
                  open: true,
                  mode: 'create',
                  team: undefined,
                })
              }
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
            >
              + Create Team
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200">
            {error}
          </div>
        )}

        <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white/80 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
          <table className="min-w-full divide-y divide-gray-100 dark:divide-gray-800">
            <thead className="bg-gray-50/80 backdrop-blur text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-gray-900/60 dark:text-gray-400">
              <tr>
                <th className="px-6 py-3">Team</th>
                <th className="px-6 py-3">Agents</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3">Updated</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white/70 text-sm dark:divide-gray-900 dark:bg-gray-900/40 dark:text-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Loading teams...
                  </td>
                </tr>
              )}
              {!isLoading && teams.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No teams yet. Create your first team to start organizing agents.
                  </td>
                </tr>
              )}
              {!isLoading &&
                teams.map((team) => (
                  <tr key={team.id}>
                    <td className="px-6 py-4">
                      <p className="font-medium text-gray-900 dark:text-white">{team.name}</p>
                      <p className="text-xs text-gray-500">ID: {team.id}</p>
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-900 dark:text-white">
                      {agentCounts[team.id] ?? 0}
                    </td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{formatDate(team.created_at)}</td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{formatDate(team.updated_at)}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setTeamModal({
                              open: true,
                              mode: 'edit',
                              team,
                            })
                          }
                          className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-600 transition hover:border-brand-500 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300 bg-white/70 dark:bg-gray-900/40"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteTeam(team)}
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 transition hover:border-red-500 dark:border-red-900 bg-white/70 dark:bg-gray-900/40"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        {teamModal.open && (
          <TeamFormModal
            open={teamModal.open}
            mode={teamModal.mode}
            initialName={teamModal.team?.name}
            onClose={() => setTeamModal((prev) => ({ ...prev, open: false }))}
            onSave={handleSaveTeam}
          />
        )}
      </div>
    </div>
  )
}
