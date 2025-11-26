/**
 * Add Behavior Dialog Component - Phase 8
 * Dialog for adding a new behavior
 */

import { useState } from 'react';
import { X } from 'lucide-react';
import { useBlueprintStore } from '../../store/blueprintStore';
import type { BehaviorType, DetectionMode, CriticalAction } from '../../store/blueprintStore';

interface AddBehaviorDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stageId: string;
  onSuccess?: (newBlueprintId?: string) => void;
}

export default function AddBehaviorDialog({ isOpen, onClose, stageId, onSuccess }: AddBehaviorDialogProps) {
  const { addBehavior } = useBlueprintStore();
  const [behaviorName, setBehaviorName] = useState('');
  const [description, setDescription] = useState('');
  const [behaviorType, setBehaviorType] = useState<BehaviorType>('required');
  const [detectionMode, setDetectionMode] = useState<DetectionMode>('semantic');
  const [weight, setWeight] = useState<number>(0);
  const [phrases, setPhrases] = useState<string>('');
  const [criticalAction, setCriticalAction] = useState<CriticalAction | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!behaviorName.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const newBlueprintId = await addBehavior(stageId, {
        behavior_name: behaviorName,
        description: description || undefined,
        behavior_type: behaviorType,
        detection_mode: detectionMode,
        phrases: detectionMode !== 'semantic' && phrases ? phrases.split('\n').filter(p => p.trim()) : undefined,
        weight: weight,
        critical_action: behaviorType === 'critical' && criticalAction ? criticalAction : undefined,
        ui_order: 0,
        metadata: {}
      });
      
      setBehaviorName('');
      setDescription('');
      setWeight(0);
      setPhrases('');
      setCriticalAction('');
      
      // Close dialog first
      onClose();
      
      // Call success callback after closing
      if (onSuccess) {
        onSuccess(newBlueprintId);
      }
    } catch (error: any) {
      console.error('Failed to add behavior:', error);
      alert(error.message || 'Failed to add behavior');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-slate-200 dark:border-slate-700">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Add Behavior</h2>
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
              Behavior Name *
            </label>
            <input
              type="text"
              value={behaviorName}
              onChange={(e) => setBehaviorName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              required
              placeholder="e.g., Greet customer, Verify identity"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Optional description or examples"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Type *
              </label>
              <select
                value={behaviorType}
                onChange={(e) => setBehaviorType(e.target.value as BehaviorType)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="required">Required</option>
                <option value="optional">Optional</option>
                <option value="forbidden">Forbidden</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Detection Mode *
              </label>
              <select
                value={detectionMode}
                onChange={(e) => setDetectionMode(e.target.value as DetectionMode)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="semantic">Semantic</option>
                <option value="exact_phrase">Exact Phrase</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>
          </div>

          {detectionMode !== 'semantic' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Phrases (one per line) *
              </label>
              <textarea
                value={phrases}
                onChange={(e) => setPhrases(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                rows={4}
                required
                placeholder="Enter phrases to match, one per line"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Weight: {weight}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={weight}
              onChange={(e) => setWeight(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {behaviorType === 'critical' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Critical Action *
              </label>
              <select
                value={criticalAction}
                onChange={(e) => setCriticalAction(e.target.value as CriticalAction)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select action</option>
                <option value="fail_stage">Fail Stage</option>
                <option value="fail_overall">Fail Overall</option>
                <option value="flag_only">Flag Only</option>
              </select>
            </div>
          )}

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
              {isSubmitting ? 'Adding...' : 'Add Behavior'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

