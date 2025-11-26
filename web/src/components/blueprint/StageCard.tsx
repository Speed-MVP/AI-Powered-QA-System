/**
 * Stage Card Component - Phase 8
 * Center canvas stage card with behaviors
 */

import { Plus, Edit2 } from 'lucide-react';
import type { Stage, Behavior } from '../../store/blueprintStore';
import BehaviorCard from './BehaviorCard';

interface StageCardProps {
  stage: Stage;
  isSelected: boolean;
  onSelect: () => void;
  onSelectBehavior: (behaviorId: string) => void;
  onAddBehavior: () => void;
}

export default function StageCard({
  stage,
  isSelected,
  onSelect,
  onSelectBehavior,
  onAddBehavior
}: StageCardProps) {
  const sortedBehaviors = [...stage.behaviors].sort((a, b) => a.ui_order - b.ui_order);

  return (
    <div
      className={`
        bg-white dark:bg-slate-800 rounded-lg shadow-md border-2 transition-all
        ${isSelected ? 'border-blue-500 dark:border-blue-400' : 'border-slate-200 dark:border-slate-700'}
      `}
    >
      {/* Stage Header */}
      <div
        onClick={onSelect}
        className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{stage.stage_name || 'Unnamed Stage'}</h3>
            {stage.stage_weight !== undefined && stage.stage_weight !== null && (
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">Weight: {stage.stage_weight}%</p>
            )}
          </div>
          <Edit2 className="w-5 h-5 text-slate-400 dark:text-slate-500" />
        </div>
      </div>

      {/* Behaviors List */}
      <div className="p-4 space-y-2">
        {sortedBehaviors.length === 0 ? (
          <div className="text-center py-8 text-slate-600 dark:text-slate-300">
            <p className="text-sm mb-2">No behaviors yet</p>
            <button
              onClick={onAddBehavior}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
            >
              Add Behavior
            </button>
          </div>
        ) : (
          <>
            {sortedBehaviors.map((behavior) => (
              <BehaviorCard
                key={behavior.id}
                behavior={behavior}
                onSelect={() => onSelectBehavior(behavior.id)}
              />
            ))}
            <button
              onClick={onAddBehavior}
              className="w-full flex items-center justify-center gap-2 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-600 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Behavior
            </button>
          </>
        )}
      </div>
    </div>
  );
}

