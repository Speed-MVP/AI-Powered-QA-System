import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { Agent, Team } from '@/lib/api'
import { AgentFormModal } from '@/components/modals/AgentFormModal'
import { BulkImportModal } from '@/components/modals/BulkImportModal'
import { ConfirmModal } from '@/components/modals'

export function AgentsListPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [agentModal, setAgentModal] = useState<{
    open: boolean
    mode: 'create' | 'edit'
    agent?: Agent
  }>({ open: false, mode: 'create' })
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [deleteConfirmModal, setDeleteConfirmModal] = useState<{ isOpen: boolean; agent: Agent } | null>(null)

  const loadDirectory = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [teamData, agentData] = await Promise.all([api.listTeams(), api.listAgents()])
      setTeams(teamData)
      setAgents(agentData)
    } catch (err: any) {
      setError(err.message || 'Failed to load agents')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDirectory()
  }, [])

  const filteredAgents = useMemo(() => {
    if (!selectedTeam) return agents
    return agents.filter((agent) => agent.team_memberships.some((membership) => membership.team_id === selectedTeam))
  }, [agents, selectedTeam])

  const handleSaveAgent = async (payload: { full_name: string; email: string; team_id?: string | null }) => {
    if (agentModal.mode === 'edit' && agentModal.agent) {
      await api.updateAgent(agentModal.agent.id, payload)
    } else {
      await api.createAgent(payload)
    }
    await loadDirectory()
  }

  const handleDeleteAgent = (agent: Agent) => {
    setDeleteConfirmModal({
      isOpen: true,
      agent,
    })
  }

  const confirmDeleteAgent = async () => {
    if (!deleteConfirmModal) return
    await api.deleteAgent(deleteConfirmModal.agent.id)
    await loadDirectory()
    setDeleteConfirmModal(null)
  }

  const getPrimaryTeam = (agent: Agent) => agent.team_memberships[0]?.team_name ?? 'Unassigned'

  const formatDate = (value: string) => new Date(value).toLocaleDateString()

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
            <p className="text-sm uppercase tracking-wide text-brand-600">Agents</p>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agent Directory</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Manage individual agents, assign teams, and run imports.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setImportModalOpen(true)}
              className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-brand-500 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300 bg-white/80 dark:bg-gray-900/60"
            >
              + Bulk Import
            </button>
            <button
              type="button"
              onClick={() =>
                setAgentModal({
                  open: true,
                  mode: 'create',
                })
              }
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
            >
              + Add Agent
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Filter by team
          </label>
          <select
            value={selectedTeam}
            onChange={(event) => setSelectedTeam(event.target.value)}
            className="mt-2 w-full rounded-xl border border-gray-200 px-4 py-2 text-sm text-gray-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white md:w-72"
          >
            <option value="">All teams</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
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
                <th className="px-6 py-3">Agent</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Team</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white/70 text-sm dark:divide-gray-900 dark:bg-gray-900/40 dark:text-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Loading agents...
                  </td>
                </tr>
              )}
              {!isLoading && filteredAgents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    {selectedTeam ? 'No agents in this team yet.' : 'No agents found. Import or add your first agent.'}
                  </td>
                </tr>
              )}
              {!isLoading &&
                filteredAgents.map((agent) => (
                  <tr key={agent.id}>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-gray-900 dark:text-white">{agent.full_name}</p>
                      <p className="text-xs text-gray-500">ID: {agent.id}</p>
                    </td>
                    <td className="px-6 py-4 text-gray-700 dark:text-gray-200">{agent.email}</td>
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">{getPrimaryTeam(agent)}</td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{formatDate(agent.created_at)}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setAgentModal({
                              open: true,
                              mode: 'edit',
                              agent,
                            })
                          }
                          className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-600 transition hover:border-brand-500 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300 bg-white/70 dark:bg-gray-900/40"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteAgent(agent)}
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

        {agentModal.open && (
          <AgentFormModal
            open={agentModal.open}
            mode={agentModal.mode}
            teams={teams}
            initialData={
              agentModal.agent
                ? {
                    full_name: agentModal.agent.full_name,
                    email: agentModal.agent.email,
                    team_id: agentModal.agent.team_memberships[0]?.team_id ?? '',
                  }
                : undefined
            }
            onClose={() => setAgentModal((prev) => ({ ...prev, open: false }))}
            onSave={handleSaveAgent}
          />
        )}

        {importModalOpen && (
          <BulkImportModal
            open={importModalOpen}
            onClose={() => setImportModalOpen(false)}
            onComplete={async () => {
              await loadDirectory()
              setImportModalOpen(false)
            }}
          />
        )}

        {/* Delete Confirmation Modal */}
        {deleteConfirmModal && (
          <ConfirmModal
            isOpen={deleteConfirmModal.isOpen}
            onClose={() => setDeleteConfirmModal(null)}
            onConfirm={confirmDeleteAgent}
            title="Remove Agent"
            message={`Remove agent "${deleteConfirmModal.agent.full_name}"?`}
            confirmText="Remove"
            cancelText="Cancel"
            confirmColor="red"
            danger
          />
        )}
      </div>
    </div>
  )
}
