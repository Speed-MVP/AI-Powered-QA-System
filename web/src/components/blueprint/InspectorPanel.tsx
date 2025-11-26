/**
 * Inspector Panel Component - Phase 8
 * Right column properties editor
 */

import type { Stage, Behavior } from '../../store/blueprintStore';
import { X } from 'lucide-react';

interface InspectorPanelProps {
  stage: Stage | null;
  behavior: Behavior | null;
  onUpdateStage: (updates: Partial<Stage>) => void;
  onUpdateBehavior: (updates: Partial<Behavior>) => void;
}

export default function InspectorPanel({
  stage,
  behavior,
  onUpdateStage,
  onUpdateBehavior
}: InspectorPanelProps) {
  if (!stage && !behavior) {
    return (
      <div className="p-6 text-center text-slate-600 dark:text-slate-300">
        <p className="text-sm">Select a stage or behavior to edit</p>
      </div>
    );
  }

  if (behavior) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Behavior Properties</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Name</label>
            <input
              type="text"
              value={behavior.behavior_name}
              onChange={(e) => onUpdateBehavior({ behavior_name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Description</label>
            <textarea
              value={behavior.description || ''}
              onChange={(e) => onUpdateBehavior({ description: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Type</label>
            <select
              value={behavior.behavior_type}
              onChange={(e) => onUpdateBehavior({ behavior_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="required">Required</option>
              <option value="optional">Optional</option>
              <option value="forbidden">Forbidden</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Detection Mode</label>
            <select
              value={behavior.detection_mode}
              onChange={(e) => onUpdateBehavior({ detection_mode: e.target.value as any })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="semantic">Semantic</option>
              <option value="exact_phrase">Exact Phrase</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Weight: {behavior.weight}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={behavior.weight}
              onChange={(e) => onUpdateBehavior({ weight: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>

          {behavior.behavior_type === 'critical' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Critical Action</label>
              <select
                value={behavior.critical_action || ''}
                onChange={(e) => onUpdateBehavior({ critical_action: e.target.value as any })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select action</option>
                <option value="fail_stage">Fail Stage</option>
                <option value="fail_overall">Fail Overall</option>
                <option value="flag_only">Flag Only</option>
              </select>
            </div>
          )}

          {behavior.detection_mode !== 'semantic' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Phrases</label>
              <textarea
                value={(behavior.phrases || []).join('\n')}
                onChange={(e) => onUpdateBehavior({
                  phrases: e.target.value.split('\n').filter(p => p.trim())
                })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder="Enter phrases, one per line"
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  if (stage) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Stage Properties</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Stage Name</label>
            <input
              type="text"
              value={stage.stage_name}
              onChange={(e) => onUpdateStage({ stage_name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Stage Weight: {stage.stage_weight || 0}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={stage.stage_weight || 0}
              onChange={(e) => onUpdateStage({ stage_weight: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>

          <div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {stage.behaviors.length} behavior{stage.behaviors.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

