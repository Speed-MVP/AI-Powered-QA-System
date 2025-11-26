/**
 * Sandbox Page - Phase 8
 * Complete sandbox testing interface
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import SandboxRunner from '../components/blueprint/SandboxRunner';
import EvaluationViewer from '../components/blueprint/EvaluationViewer';
import TranscriptPlayer from '../components/blueprint/TranscriptPlayer';

interface SandboxResult {
  run_id: string;
  status: string;
  result?: {
    final_evaluation?: any;
    detection_output?: any;
    transcript_snapshot?: any;
    cost_estimate?: any;
  };
}

export default function SandboxPage() {
  const { blueprintId } = useParams<{ blueprintId: string }>();
  const navigate = useNavigate();
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [sandboxResult, setSandboxResult] = useState<SandboxResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [transcriptSegments, setTranscriptSegments] = useState<any[]>([]);
  const [behaviorMatches, setBehaviorMatches] = useState<any[]>([]);

  useEffect(() => {
    if (activeRunId && blueprintId) {
      loadSandboxResult(activeRunId);
    }
  }, [activeRunId, blueprintId]);

  const loadSandboxResult = async (runId: string) => {
    if (!blueprintId) return;

    setLoading(true);
    try {
      const result = await api.getSandboxRun(blueprintId, runId);
      setSandboxResult(result);

      // Extract transcript segments from result
      if (result.result?.transcript_snapshot) {
        // In production, would load full transcript from snapshot or recording
        // For now, use placeholder
        setTranscriptSegments([]);
      }

      // Extract behavior matches from detection output
      if (result.result?.detection_output?.behaviors) {
        const matches = result.result.detection_output.behaviors
          .filter((b: any) => b.detected)
          .map((b: any) => ({
            behavior_id: b.behavior_id,
            behavior_name: b.behavior_name,
            matched_text: b.matched_text || '',
            start_time: b.start_time || 0,
            end_time: b.end_time || 0,
            confidence: b.confidence || 0,
            violation: b.violation || false
          }));
        setBehaviorMatches(matches);
      }
    } catch (error: any) {
      console.error('Failed to load sandbox result:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunComplete = (runId: string) => {
    setActiveRunId(runId);
    loadSandboxResult(runId);
  };

  if (!blueprintId) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <p className="text-slate-600 dark:text-slate-400">Blueprint ID not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => navigate(`/blueprints/${blueprintId}`)}
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Sandbox Testing</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">Test your blueprint against sample transcripts or recordings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Sandbox Runner */}
          <div>
            <SandboxRunner
              blueprintId={blueprintId}
              onRunComplete={handleRunComplete}
            />
          </div>

          {/* Right Column: Results */}
          <div>
            {loading ? (
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-12 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-slate-600 dark:text-slate-400">Loading results...</p>
              </div>
            ) : sandboxResult ? (
              <EvaluationViewer result={sandboxResult} />
            ) : (
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-12 text-center">
                <p className="text-slate-500 dark:text-slate-400">Run an evaluation to see results here</p>
              </div>
            )}
          </div>
        </div>

        {/* Transcript Player (if results available) */}
        {sandboxResult && sandboxResult.status === 'succeeded' && (
          <div className="mt-6">
            <TranscriptPlayer
              segments={transcriptSegments}
              behaviorMatches={behaviorMatches}
            />
          </div>
        )}
      </div>
    </div>
  );
}

