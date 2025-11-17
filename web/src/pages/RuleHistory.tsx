/**
 * Rule History Page
 * Phase 5: Structured Rule Editor UI & Admin Tools
 * 
 * Shows draft list and version history with diff viewer.
 * Allows rollback to previous versions.
 */

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { FaHistory, FaUndo } from 'react-icons/fa'

export function RuleHistory() {
  const { templateId } = useParams<{ templateId: string }>()
  const [history, setHistory] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (templateId) {
      loadHistory()
    }
  }, [templateId])

  const loadHistory = async () => {
    if (!templateId) return
    
    try {
      const data = await api.get(`/api/policy-templates/${templateId}/rules/history`)
      setHistory(data)
    } catch (err: any) {
      console.error('Failed to load history:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRollback = async (versionId: string) => {
    if (!templateId) return
    
    if (!confirm('Create a draft from this version? You will need to publish it to activate.')) {
      return
    }

    try {
      await api.post(`/api/policy-templates/${templateId}/rules/rollback`, {
        version_id: versionId,
        reason: 'Rollback from history page'
      })
      alert('Rollback draft created successfully')
      loadHistory()
    } catch (err: any) {
      alert(`Failed to rollback: ${err.message}`)
    }
  }

  if (loading) {
    return <div className="p-8">Loading history...</div>
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <FaHistory /> Rule History
      </h1>

      {/* Versions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Published Versions</h2>
        <div className="space-y-2">
          {history?.versions?.map((version: any) => (
            <div key={version.id} className="border p-4 rounded flex items-center justify-between">
              <div>
                <div className="font-medium">Version {version.rules_version}</div>
                <div className="text-sm text-gray-600">
                  Created: {new Date(version.created_at).toLocaleString()} by {version.created_by}
                </div>
                <div className="text-xs text-gray-500">Hash: {version.rules_hash.substring(0, 16)}...</div>
              </div>
              <button
                onClick={() => handleRollback(version.id)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
              >
                <FaUndo /> Rollback
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Drafts */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Drafts</h2>
        <div className="space-y-2">
          {history?.drafts?.map((draft: any) => (
            <div key={draft.id} className="border p-4 rounded">
              <div className="font-medium">Draft {draft.id.substring(0, 8)}...</div>
              <div className="text-sm text-gray-600">
                Status: {draft.status} | Created: {new Date(draft.created_at).toLocaleString()} by {draft.created_by}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

