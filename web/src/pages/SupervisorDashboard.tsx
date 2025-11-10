import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { Agent, AuditLogEntry, Team } from '@/lib/api'

interface DashboardStats {
  teamCount: number
  agentCount: number
  evaluationCount: number | null
}

export function SupervisorDashboard() {
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([])
  const [stats, setStats] = useState<DashboardStats>({
    teamCount: 0,
    agentCount: 0,
    evaluationCount: null,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDashboard = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [teamData, agentData, auditData, evaluationSummary] = await Promise.all([
        api.listTeams(),
        api.listAgents(),
        api.getAuditLog({ limit: 5 }),
        api.getSupervisorEvaluations({ limit: 1 }),
      ])
      setTeams(teamData)
      setAgents(agentData)
      setAuditLog(auditData)
      setStats({
        teamCount: teamData.length,
        agentCount: agentData.length,
        evaluationCount: evaluationSummary.pagination?.total ?? null,
      })
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  const latestAgent = useMemo(() => {
    return [...agents].sort((a, b) => (b.created_at > a.created_at ? 1 : -1))[0]
  }, [agents])

  const latestTeam = useMemo(() => {
    return [...teams].sort((a, b) => ((b.created_at ?? '') > (a.created_at ?? '') ? 1 : -1))[0]
  }, [teams])

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
            <p className="text-sm uppercase tracking-wide text-brand-600">Supervisor</p>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Operations Overview</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">High-level pulse on teams, agents, and recent governance changes.</p>
          </div>
          <button
            type="button"
            onClick={loadDashboard}
            className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-brand-500 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300 bg-white/80 dark:bg-gray-900/60"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200">
            {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          <StatCard title="Total Teams" value={stats.teamCount.toString()} subtitle="Active in this org" />
          <StatCard title="Total Agents" value={stats.agentCount.toString()} subtitle="Provisioned users" />
          <StatCard
            title="Total Evaluations"
            value={stats.evaluationCount !== null ? stats.evaluationCount.toString() : '—'}
            subtitle={stats.evaluationCount !== null ? 'Supervisor API total' : 'Connect evaluation summary API'}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-gray-100 bg-white/80 p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Latest Directory Activity</h2>
            <div className="mt-4 space-y-3 text-sm text-gray-600 dark:text-gray-300">
              <p>
                <span className="text-gray-400">Last team created:</span>{' '}
                {latestTeam ? `${latestTeam.name} (${new Date(latestTeam.created_at ?? '').toLocaleDateString()})` : '—'}
              </p>
              <p>
                <span className="text-gray-400">Last agent added:</span>{' '}
                {latestAgent
                  ? `${latestAgent.full_name} • ${latestAgent.email}`
                  : '—'}
              </p>
              <p>
                <span className="text-gray-400">Audit trail coverage:</span> {auditLog.length} entries fetched
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white/80 p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Audit Events</h2>
            <div className="mt-4 space-y-4">
              {auditLog.length === 0 && (
                <p className="text-sm text-gray-500">No recent activity.</p>
              )}
              {auditLog.map((entry) => (
                <div key={entry.id} className="rounded-xl border border-gray-100 p-3 text-sm dark:border-gray-800 bg-white/70 dark:bg-gray-900/40">
                  <p className="text-xs uppercase tracking-wide text-gray-400">
                    {new Date(entry.changed_at).toLocaleString()}
                  </p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {entry.change_type} {entry.entity_type} ({entry.entity_id})
                  </p>
                  {entry.field_name && (
                    <p className="text-gray-600 dark:text-gray-300">
                      {entry.field_name}: <span className="line-through">{entry.old_value || '—'}</span> →{' '}
                      <span className="font-medium">{entry.new_value || '—'}</span>
                    </p>
                  )}
                  <p className="text-xs text-gray-500">Changed by {entry.changed_by}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {isLoading && (
          <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 text-center text-sm text-gray-500 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
            Loading supervisor metrics...
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-white/80 p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}
