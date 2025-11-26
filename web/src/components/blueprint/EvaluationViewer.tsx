/**
 * Evaluation Viewer Component - Phase 8
 * Displays sandbox evaluation results
 */

import { useState } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';

interface EvaluationResult {
  run_id: string;
  status: string;
  result?: {
    final_evaluation?: {
      overall_score: number;
      overall_passed: boolean;
      stage_scores?: Array<{
        stage_id: string;
        stage_name: string;
        score: number;
        weight: number;
        confidence: number;
      }>;
      policy_violations?: Array<{
        rule_id: string;
        severity: string;
        description: string;
      }>;
      penalty_breakdown?: Array<{
        rule_id: string;
        severity: string;
        penalty_points: number;
        reason: string;
      }>;
    };
    detection_output?: {
      behaviors?: Array<{
        behavior_id: string;
        behavior_name: string;
        detected: boolean;
        confidence: number;
        violation: boolean;
      }>;
    };
    cost_estimate?: {
      estimated_cost: number;
      tokens_used?: number;
    };
  };
}

interface EvaluationViewerProps {
  result: EvaluationResult;
}

export default function EvaluationViewer({ result }: EvaluationViewerProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'stages' | 'behaviors' | 'violations'>('summary');

  if (!result.result) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-6">
        <p className="text-slate-500 dark:text-slate-400">No evaluation results available</p>
      </div>
    );
  }

  const finalEval = result.result.final_evaluation;
  if (!finalEval) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-6">
        <p className="text-slate-500 dark:text-slate-400">Evaluation is still processing...</p>
      </div>
    );
  }

  const overallScore = finalEval.overall_score || 0;
  const overallPassed = finalEval.overall_passed || false;
  
  // Handle stage_scores as either array or object
  const stageScoresRaw = finalEval.stage_scores || [];
  const stageScores = Array.isArray(stageScoresRaw)
    ? stageScoresRaw
    : Object.keys(stageScoresRaw).map(key => ({
        stage_id: key,
        stage_name: stageScoresRaw[key].name || stageScoresRaw[key].stage_name || `Stage ${key}`,
        score: stageScoresRaw[key].score || 0,
        weight: stageScoresRaw[key].weight || 0,
        confidence: stageScoresRaw[key].confidence || 0,
        passed: stageScoresRaw[key].passed,
        feedback: stageScoresRaw[key].feedback
      }));
  
  const violations = finalEval.policy_violations || [];
  const behaviors = result.result.detection_output?.behaviors || [];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Evaluation Results</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Run ID: {result.run_id}</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{overallScore}</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Overall Score</div>
            </div>
            <div className={`p-3 rounded-lg ${overallPassed ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
              {overallPassed ? (
                <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700 px-6">
        <div className="flex gap-4">
          {[
            { id: 'summary', label: 'Summary' },
            { id: 'stages', label: 'Stages' },
            { id: 'behaviors', label: 'Behaviors' },
            { id: 'violations', label: 'Violations' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Score Breakdown */}
            <div>
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Score Breakdown</h4>
              <div className="space-y-2">
                {stageScores.map((stage) => (
                  <div key={stage.stage_id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-900 dark:text-white">{stage.stage_name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Weight: {stage.weight}%</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-lg font-semibold text-slate-900 dark:text-white">{stage.score}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Confidence: {(stage.confidence * 100).toFixed(0)}%</div>
                      </div>
                      {stage.score >= 70 ? (
                        <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cost Estimate */}
            {result.result.cost_estimate && (
              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Cost Estimate</h4>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  Estimated Cost: ${result.result.cost_estimate.estimated_cost.toFixed(4)}
                  {result.result.cost_estimate.tokens_used && (
                    <span className="ml-4">Tokens: {result.result.cost_estimate.tokens_used.toLocaleString()}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stages' && (
          <div className="space-y-4">
            {stageScores.map((stage) => (
              <div key={stage.stage_id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-slate-900 dark:text-white">{stage.stage_name}</h4>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{stage.score}</span>
                    <span className="text-sm text-slate-500 dark:text-slate-400">/ 100</span>
                  </div>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      stage.score >= 70 ? 'bg-green-600 dark:bg-green-500' : stage.score >= 50 ? 'bg-yellow-600 dark:bg-yellow-500' : 'bg-red-600 dark:bg-red-500'
                    }`}
                    style={{ width: `${stage.score}%` }}
                  />
                </div>
                <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                  Weight: {stage.weight}% | Confidence: {(stage.confidence * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'behaviors' && (
          <div className="space-y-2">
            {behaviors.length === 0 ? (
              <p className="text-slate-500 dark:text-slate-400 text-center py-8">No behavior detection results available</p>
            ) : (
              behaviors.map((behavior) => (
                <div
                  key={behavior.behavior_id}
                  className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-900 dark:text-white">{behavior.behavior_name}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Confidence: {(behavior.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {behavior.detected ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                    )}
                    {behavior.violation && (
                      <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'violations' && (
          <div className="space-y-3">
            {violations.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-2" />
                <p className="text-slate-500 dark:text-slate-400">No policy violations detected</p>
              </div>
            ) : (
              violations.map((violation, index) => (
                <div
                  key={index}
                  className="border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 rounded-lg p-4"
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          violation.severity === 'critical' ? 'bg-red-600 text-white' :
                          violation.severity === 'major' ? 'bg-orange-600 text-white' :
                          'bg-yellow-600 text-white'
                        }`}>
                          {violation.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">Rule: {violation.rule_id}</span>
                      </div>
                      <p className="text-sm text-slate-900 dark:text-white">{violation.description}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

