/**
 * Behavior Card Component - Phase 8
 * Behavior summary row with type badge and weight
 */

import type { Behavior } from '../../store/blueprintStore';

interface BehaviorCardProps {
  behavior: Behavior;
  onSelect: () => void;
}

export default function BehaviorCard({ behavior, onSelect }: BehaviorCardProps) {
  const getTypeColor = (type: string) => {
    const colors = {
      required: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      optional: 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200',
      forbidden: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      critical: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300'
    };
    return colors[type as keyof typeof colors] || colors.optional;
  };

  return (
    <div
      onClick={onSelect}
      className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(behavior.behavior_type)}`}>
              {behavior.behavior_type}
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-300">{behavior.detection_mode}</span>
          </div>
          <h4 className="text-sm font-medium text-slate-900 dark:text-white truncate">
            {behavior.behavior_name}
          </h4>
          {behavior.description && (
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 line-clamp-2">{behavior.description}</p>
          )}
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">{behavior.weight}%</div>
          {behavior.critical_action && (
            <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
              {behavior.critical_action.replace('_', ' ')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

