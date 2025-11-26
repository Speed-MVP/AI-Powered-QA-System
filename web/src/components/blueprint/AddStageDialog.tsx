/**
 * Add Stage Dialog Component - Phase 8
 * Dialog for adding a new stage
 */

import { useState } from 'react';
import { X } from 'lucide-react';
import { useBlueprintStore } from '../../store/blueprintStore';

interface AddStageDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (newBlueprintId?: string) => void;
}

export default function AddStageDialog({ isOpen, onClose, onSuccess }: AddStageDialogProps) {
  const { currentBlueprint, addStage } = useBlueprintStore();
  const [stageName, setStageName] = useState('');
  const [stageWeight, setStageWeight] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!currentBlueprint || !stageName.trim() || isSubmitting) return;

    const maxOrdering = Math.max(
      ...currentBlueprint.stages.map(s => s.ordering_index),
      0
    );

    setIsSubmitting(true);
    try {
      const newBlueprintId = await addStage({
        stage_name: stageName,
        ordering_index: maxOrdering + 1,
        stage_weight: stageWeight || undefined,
        metadata: {},
        behaviors: []
      });
      
      setStageName('');
      setStageWeight(0);
      
      // Close dialog first
      onClose();
      
      // Call success callback after closing
      if (onSuccess) {
        onSuccess(newBlueprintId);
      }
    } catch (error: any) {
      console.error('Failed to add stage:', error);
      alert(error.message || 'Failed to add stage');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full mx-4 border border-slate-200 dark:border-slate-700">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Add Stage</h2>
          <button
            onClick={onClose}
            className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Stage Name *
            </label>
            <input
              type="text"
              value={stageName}
              onChange={(e) => setStageName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              required
              placeholder="e.g., Opening, Verification, Resolution"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Stage Weight (%)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={stageWeight}
              onChange={(e) => setStageWeight(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Optional. Stage weights should sum to 100% across all stages.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Adding...' : 'Add Stage'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

