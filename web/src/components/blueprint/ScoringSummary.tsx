/**
 * Scoring Summary Component - Phase 8
 * Bottom bar showing stage weights and validation
 */

import { AlertCircle, CheckCircle2 } from 'lucide-react';
import type { Stage } from '../../store/blueprintStore';

interface ScoringSummaryProps {
  stages: Stage[];
}

export default function ScoringSummary({ stages }: ScoringSummaryProps) {
  const totalWeight = stages.reduce((sum, stage) => {
    const weight = Number(stage.stage_weight) || 0;
    return sum + weight;
  }, 0);
  const isValid = Math.abs(totalWeight - 100) < 0.01;

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div>
          <span className="text-sm text-slate-700 dark:text-slate-300">Total Stage Weight: </span>
          <span className={`text-sm font-semibold ${isValid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {totalWeight.toFixed(1)}%
          </span>
        </div>
        {isValid ? (
          <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-sm">Valid</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">Must equal 100%</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        {stages.map((stage, index) => (
          <div key={stage.id} className="flex items-center gap-1">
            <div
              className="h-4 bg-blue-500 dark:bg-blue-400"
              style={{ width: `${(stage.stage_weight || 0) * 2}px`, minWidth: '4px' }}
              title={`${stage.stage_name}: ${stage.stage_weight || 0}%`}
            />
            {index < stages.length - 1 && <span className="text-slate-300 dark:text-slate-600">|</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

