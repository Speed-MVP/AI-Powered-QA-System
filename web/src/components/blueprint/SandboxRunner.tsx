/**
 * Sandbox Runner Component - Phase 8
 * Component for running sandbox evaluations
 */

import { useState } from 'react';
import { Play, Upload, FileText, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../../lib/api';

interface SandboxRunnerProps {
  blueprintId: string;
  onRunComplete?: (runId: string) => void;
}

export default function SandboxRunner({ blueprintId, onRunComplete }: SandboxRunnerProps) {
  const [mode, setMode] = useState<'transcript' | 'audio'>('transcript');
  const [transcript, setTranscript] = useState('');
  const [recordingId, setRecordingId] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (mode === 'transcript' && !transcript.trim()) {
      setError('Please enter a transcript');
      return;
    }

    if (mode === 'audio' && !recordingId) {
      setError('Please select a recording');
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const response = await api.sandboxEvaluate(blueprintId, {
        mode: mode === 'transcript' ? 'sync' : 'async',
        input: {
          transcript: mode === 'transcript' ? transcript : undefined,
          recording_id: mode === 'audio' ? recordingId : undefined
        }
      });

      setRunId(response.run_id);
      
      if (response.status === 'succeeded' && onRunComplete) {
        onRunComplete(response.run_id);
      } else if (response.status === 'queued') {
        // Poll for completion
        pollRunStatus(response.run_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to run sandbox evaluation');
      setIsRunning(false);
    }
  };

  const pollRunStatus = async (runId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await api.getSandboxRun(blueprintId, runId);
        
        if (status.status === 'succeeded') {
          setIsRunning(false);
          if (onRunComplete) {
            onRunComplete(runId);
          }
        } else if (status.status === 'failed') {
          setIsRunning(false);
          setError('Sandbox evaluation failed');
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setIsRunning(false);
          setError('Sandbox evaluation timed out');
        }
      } catch (err: any) {
        setIsRunning(false);
        setError(err.message || 'Failed to check sandbox status');
      }
    };

    poll();
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Run Sandbox Evaluation</h3>

      {/* Mode Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Input Type</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="transcript"
              checked={mode === 'transcript'}
              onChange={(e) => setMode(e.target.value as 'transcript' | 'audio')}
              className="w-4 h-4 text-blue-600"
            />
            <FileText className="w-5 h-5 text-slate-400 dark:text-slate-500" />
            <span className="text-sm text-slate-700 dark:text-slate-300">Transcript</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="audio"
              checked={mode === 'audio'}
              onChange={(e) => setMode(e.target.value as 'transcript' | 'audio')}
              className="w-4 h-4 text-blue-600"
            />
            <Upload className="w-5 h-5 text-slate-400 dark:text-slate-500" />
            <span className="text-sm text-slate-700 dark:text-slate-300">Audio Recording</span>
          </label>
        </div>
      </div>

      {/* Transcript Input */}
      {mode === 'transcript' && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Transcript Text
          </label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            rows={8}
            placeholder="Paste transcript here...&#10;&#10;Agent: Hello, how can I help you today?&#10;Customer: I need help with my account..."
          />
        </div>
      )}

      {/* Recording Selection */}
      {mode === 'audio' && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Recording ID
          </label>
          <input
            type="text"
            value={recordingId}
            onChange={(e) => setRecordingId(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            placeholder="Enter recording ID or select from recordings..."
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            You can find recording IDs in the Recordings page
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
          <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Run Status */}
      {runId && (
        <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-center gap-2">
          {isRunning ? (
            <>
              <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
              <span className="text-sm text-blue-800 dark:text-blue-300">Running evaluation... Run ID: {runId}</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-sm text-green-800 dark:text-green-300">Evaluation completed. Run ID: {runId}</span>
            </>
          )}
        </div>
      )}

      {/* Run Button */}
      <button
        onClick={handleRun}
        disabled={isRunning || (mode === 'transcript' && !transcript.trim()) || (mode === 'audio' && !recordingId)}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isRunning ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Running...
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            Run Evaluation
          </>
        )}
      </button>

      <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 text-center">
        {mode === 'transcript' 
          ? 'Transcript evaluations run synchronously and return results immediately'
          : 'Audio evaluations run asynchronously and may take a few minutes'}
      </p>
    </div>
  );
}

