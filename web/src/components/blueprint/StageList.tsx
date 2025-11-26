/**
 * Stage List Component - Phase 8
 * Left column stage list with drag handles
 */

import { GripVertical, Plus } from 'lucide-react';
import type { Stage } from '../../store/blueprintStore';

interface StageListProps {
  stages: Stage[];
  selectedStageId: string | null;
  onSelectStage: (stageId: string) => void;
  onReorderStages: (stageIds: string[]) => void;
  onAddStage?: () => void;
}

export default function StageList({
  stages,
  selectedStageId,
  onSelectStage,
  onReorderStages,
  onAddStage
}: StageListProps) {
  const sortedStages = [...stages].sort((a, b) => a.ordering_index - b.ordering_index);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase">Stages</h2>
        <button
          onClick={onAddStage}
          className="p-1 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
          title="Add Stage"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-1">
        {sortedStages.map((stage) => (
          <div
            key={stage.id}
            onClick={() => onSelectStage(stage.id)}
            className={`
              flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors
              ${selectedStageId === stage.id
                ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }
            `}
          >
            <GripVertical className="w-4 h-4 text-slate-400 dark:text-slate-500 cursor-move" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {stage.stage_name || 'Unnamed Stage'}
              </div>
              {stage.stage_weight !== undefined && stage.stage_weight !== null && (
                <div className="text-xs text-slate-600 dark:text-slate-300">
                  {stage.stage_weight}%
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

