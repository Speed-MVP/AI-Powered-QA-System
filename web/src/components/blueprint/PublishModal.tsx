/**
 * Publish Modal Component - Phase 8
 * Validation checklist and publish button
 */

import { useState, useEffect } from 'react';
import { X, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { api } from '../../lib/api';

interface PublishModalProps {
  blueprintId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PublishModal({ blueprintId, onClose, onSuccess }: PublishModalProps) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [publishStatus, setPublishStatus] = useState<any>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const handlePublish = async () => {
    try {
      setIsPublishing(true);
      const response = await api.publishBlueprint(blueprintId, {
        force_normalize_weights: false
      });
      setJobId(response.job_id);
      
      // Poll for status
      pollPublishStatus(blueprintId, response.job_id);
    } catch (error: any) {
      setErrors([error.message || 'Publish failed']);
      setIsPublishing(false);
    }
  };

  const pollPublishStatus = async (blueprintId: string, jobId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await api.getPublishStatus(blueprintId, jobId);
        setPublishStatus(status);

        if (status.status === 'succeeded') {
          setIsPublishing(false);
          setTimeout(() => {
            onSuccess();
          }, 1000);
        } else if (status.status === 'failed') {
          setIsPublishing(false);
          setErrors(status.errors?.map((e: any) => e.message) || ['Publish failed']);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setIsPublishing(false);
          setErrors(['Publish timed out']);
        }
      } catch (error: any) {
        setIsPublishing(false);
        setErrors([error.message || 'Failed to check publish status']);
      }
    };

    poll();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-slate-200 dark:border-slate-700">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Publish Blueprint</h2>
          <button
            onClick={onClose}
            className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {errors.length > 0 && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-red-900 dark:text-red-300 mb-2">Validation Errors</h3>
                  <ul className="list-disc list-inside text-sm text-red-800 dark:text-red-300 space-y-1">
                    {errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {publishStatus && publishStatus.status === 'running' && (
            <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                <span className="text-blue-900 dark:text-blue-300">Publishing... {publishStatus.progress}%</span>
              </div>
            </div>
          )}

          {publishStatus && publishStatus.status === 'succeeded' && (
            <div className="mb-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-green-900 dark:text-green-300">Blueprint published successfully!</span>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <p className="text-slate-600 dark:text-slate-400">
              Publishing will compile your blueprint and make it available for evaluations.
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
                disabled={isPublishing}
              >
                Cancel
              </button>
              <button
                onClick={handlePublish}
                disabled={isPublishing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isPublishing && <Loader2 className="w-4 h-4 animate-spin" />}
                {isPublishing ? 'Publishing...' : 'Publish'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

