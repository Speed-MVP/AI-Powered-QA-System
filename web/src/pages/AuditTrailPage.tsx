import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { Agent, AuditLogEntry, Team } from '@/lib/api'

export function AuditTrailPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    teamId: '',
    agentId: '',
    entityType: '',
    dateFrom: '',
    dateTo: '',
    limit: 100,
  })

  const loadFiltersData = async () => {
    const [teamData, agentData] = await Promise.all([api.listTeams(), api.listAgents()])
    setTeams(teamData)
    setAgents(agentData)
  }

  const loadAuditLog = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await api.getAuditLog({
        teamId: filters.teamId || undefined,
        agentId: filters.agentId || undefined,
        entityType: filters.entityType || undefined,
        dateFrom: filters.dateFrom ? new Date(filters.dateFrom).toISOString() : undefined,
        dateTo: filters.dateTo ? new Date(filters.dateTo).toISOString() : undefined,
        limit: filters.limit,
      })
      setEntries(response)
    } catch (err: any) {
      setError(err.message || 'Failed to load audit log')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadFiltersData()
    loadAuditLog()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyFilters = async () => {
    await loadAuditLog()
  }

  const exportCsv = () => {
    if (!entries.length) return
    const headers = ['entity_type', 'entity_id', 'change_type', 'field', 'old_value', 'new_value', 'changed_by', 'timestamp']
    const rows = entries.map((entry) => [
      entry.entity_type,
      entry.entity_id,
      entry.change_type,
      entry.field_name ?? '',
      entry.old_value ?? '',
      entry.new_value ?? '',
      entry.changed_by,
      entry.changed_at,
    ])
    const csv = [headers.join(','), ...rows.map((row) => row.map((value) => `"${value?.replace(/"/g, '""')}"`).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit-log-${new Date().toISOString()}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const agentOptions = useMemo(
    () => agents.map((agent) => ({ id: agent.id, label: `${agent.full_name} (${agent.email})` })),
    [agents],
  )

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
            <p className="text-sm uppercase tracking-wide text-brand-600">Audit Log</p>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agent & Team Activity</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Immutable change history across teams, agents, and memberships.</p>
          </div>
          <button
            type="button"
            onClick={exportCsv}
            className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-brand-500 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300 bg-white/80 dark:bg-gray-900/60"
            disabled={!entries.length}
          >
            Export CSV
          </button>
        </div>

        <div className="grid gap-4 rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900/60 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Team</label>
            <select
              value={filters.teamId}
              onChange={(event) => setFilters((prev) => ({ ...prev, teamId: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value="">All teams</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Agent</label>
            <select
              value={filters.agentId}
              onChange={(event) => setFilters((prev) => ({ ...prev, agentId: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value="">All agents</option>
              {agentOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Entity Type</label>
            <select
              value={filters.entityType}
              onChange={(event) => setFilters((prev) => ({ ...prev, entityType: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value="">All</option>
              <option value="agent">Agent</option>
              <option value="team">Team</option>
              <option value="membership">Membership</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">From</label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(event) => setFilters((prev) => ({ ...prev, dateFrom: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">To</label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(event) => setFilters((prev) => ({ ...prev, dateTo: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Limit</label>
            <input
              type="number"
              min={10}
              max={500}
              value={filters.limit}
              onChange={(event) => setFilters((prev) => ({ ...prev, limit: Number(event.target.value) }))}
              className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div className="md:col-span-2 lg:col-span-3">
            <button
              type="button"
              onClick={applyFilters}
              className="w-full rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
            >
              Apply Filters
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
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Change</th>
                <th className="px-4 py-3">Field</th>
                <th className="px-4 py-3">Old Value</th>
                <th className="px-4 py-3">New Value</th>
                <th className="px-4 py-3">Changed By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white/70 text-sm dark:divide-gray-900 dark:bg-gray-900/40 dark:text-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-500">
                    Loading audit log...
                  </td>
                </tr>
              )}
              {!isLoading && entries.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-500">
                    No changes match the selected filters.
                  </td>
                </tr>
              )}
              {!isLoading &&
                entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-4 py-3">{new Date(entry.changed_at).toLocaleString()}</td>
                    <td className="px-4 py-3 font-semibold">
                      {entry.entity_type} <span className="text-xs text-gray-500">({entry.entity_id})</span>
                    </td>
                    <td className="px-4 py-3 capitalize">{entry.change_type}</td>
                    <td className="px-4 py-3">{entry.field_name ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500">{entry.old_value ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-900 dark:text-white">{entry.new_value ?? '—'}</td>
                    <td className="px-4 py-3">{entry.changed_by}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
