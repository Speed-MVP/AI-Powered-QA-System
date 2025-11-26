/**
 * Blueprint Editor Canvas - Phase 8
 * Main editor with three-column layout: Stage list / Canvas / Inspector
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useBlueprintStore } from '../store/blueprintStore';
import { Save, Send, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';
import StageList from '../components/blueprint/StageList';
import StageCard from '../components/blueprint/StageCard';
import InspectorPanel from '../components/blueprint/InspectorPanel';
import ScoringSummary from '../components/blueprint/ScoringSummary';
import PublishModal from '../components/blueprint/PublishModal';
import AddStageDialog from '../components/blueprint/AddStageDialog';
import AddBehaviorDialog from '../components/blueprint/AddBehaviorDialog';
import { Beaker } from 'lucide-react';

export default function BlueprintEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentBlueprint,
    isDirty,
    lastSavedAt,
    isLoading,
    error,
    loadBlueprint,
    createBlueprint,
    initializeNewBlueprint,
    saveBlueprint,
    reset
  } = useBlueprintStore();

  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);
  const [selectedBehaviorId, setSelectedBehaviorId] = useState<string | null>(null);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showAddStageDialog, setShowAddStageDialog] = useState(false);
  const [showAddBehaviorDialog, setShowAddBehaviorDialog] = useState(false);
  const [addBehaviorStageId, setAddBehaviorStageId] = useState<string | null>(null);
  const [autoSaveTimer, setAutoSaveTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (id && id !== 'new') {
      loadBlueprint(id);
    } else if (id === 'new') {
      initializeNewBlueprint();
    } else {
      reset();
    }

    return () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }
    };
  }, [id, loadBlueprint, initializeNewBlueprint, reset]);

  // Auto-save with debounce (only for existing blueprints)
  useEffect(() => {
    if (isDirty && currentBlueprint && id && id !== 'new' && currentBlueprint.id !== 'new') {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }

      const timer = setTimeout(() => {
        saveBlueprint().catch(console.error);
      }, 2000);

      setAutoSaveTimer(timer);
    }

    return () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }
    };
  }, [isDirty, currentBlueprint, id]);

  if (isLoading && !currentBlueprint) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400">Loading blueprint...</p>
        </div>
      </div>
    );
  }

  if (!currentBlueprint) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600 dark:text-slate-400 mb-4">Blueprint not found</p>
          <button
            onClick={() => navigate('/blueprints')}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Back to Blueprints
          </button>
        </div>
      </div>
    );
  }

  const selectedStage = currentBlueprint.stages.find(s => s.id === selectedStageId);
  const selectedBehavior = selectedStage?.behaviors.find(b => b.id === selectedBehaviorId);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Toolbar */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-full flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/blueprints')}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <input
                type="text"
                value={currentBlueprint.name || ''}
                onChange={(e) => useBlueprintStore.getState().updateBlueprint({ name: e.target.value })}
                className="text-2xl font-bold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
                placeholder="Untitled Blueprint"
              />
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  currentBlueprint.status === 'published' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' :
                  currentBlueprint.status === 'draft' ? 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200' :
                  'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                }`}>
                  {currentBlueprint.status}
                </span>
                <span className="text-sm text-slate-600 dark:text-slate-300">v{currentBlueprint.version_number}</span>
                {isDirty && (
                  <span className="text-sm text-amber-600 dark:text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    Unsaved changes
                  </span>
                )}
                {lastSavedAt && !isDirty && (
                  <span className="text-sm text-slate-600 dark:text-slate-300 flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Saved {lastSavedAt.toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(`/blueprints/${currentBlueprint.id}/sandbox`)}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              title="Test blueprint in sandbox"
              disabled={id === 'new' || currentBlueprint.id === 'new'}
            >
              <Beaker className="w-4 h-4" />
              Sandbox
            </button>
            <button
              onClick={async () => {
                if (id === 'new' || currentBlueprint.id === 'new') {
                  // Create new blueprint
                  if (!currentBlueprint.name.trim()) {
                    alert('Please enter a blueprint name');
                    return;
                  }
                  try {
                    const newId = await createBlueprint(
                      currentBlueprint.name,
                      currentBlueprint.description
                    );
                    navigate(`/blueprints/${newId}`, { replace: true });
                  } catch (error: any) {
                    alert(`Failed to create blueprint: ${error.message}`);
                  }
                } else {
                  // Save existing blueprint
                  await saveBlueprint();
                }
              }}
              disabled={isLoading || (id !== 'new' && currentBlueprint.id !== 'new' && !isDirty)}
              className="flex items-center gap-2 bg-slate-600 dark:bg-slate-700 text-white px-4 py-2 rounded-lg hover:bg-slate-700 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {id === 'new' || currentBlueprint.id === 'new' ? 'Create' : 'Save'}
            </button>
            <button
              onClick={() => setShowPublishModal(true)}
              disabled={currentBlueprint.status === 'published' || isLoading || (id === 'new' || currentBlueprint.id === 'new')}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
              Publish
            </button>
          </div>
        </div>
        {error && (
          <div className="mt-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-2 rounded">
            {error}
          </div>
        )}
      </div>

      {/* Main Content - Three Columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Stage List */}
        <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 overflow-y-auto">
          <StageList
            stages={currentBlueprint.stages}
            selectedStageId={selectedStageId}
            onSelectStage={setSelectedStageId}
            onReorderStages={(stageIds) => {
              useBlueprintStore.getState().reorderStages(stageIds);
            }}
            onAddStage={() => setShowAddStageDialog(true)}
          />
        </div>

        {/* Center: Canvas */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-4xl mx-auto space-y-6">
            {currentBlueprint.stages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-600 dark:text-slate-300 mb-4">No stages yet. Add your first stage to get started.</p>
                <button
                  onClick={() => setShowAddStageDialog(true)}
                  className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add Stage
                </button>
              </div>
            ) : (
              currentBlueprint.stages
                .sort((a, b) => a.ordering_index - b.ordering_index)
                .map((stage) => (
                  <StageCard
                    key={stage.id}
                    stage={stage}
                    isSelected={stage.id === selectedStageId}
                    onSelect={() => {
                      setSelectedStageId(stage.id);
                      setSelectedBehaviorId(null);
                    }}
                    onSelectBehavior={(behaviorId) => {
                      setSelectedStageId(stage.id);
                      setSelectedBehaviorId(behaviorId);
                    }}
                    onAddBehavior={() => {
                      setAddBehaviorStageId(stage.id);
                      setShowAddBehaviorDialog(true);
                    }}
                  />
                ))
            )}
          </div>
        </div>

        {/* Right: Inspector Panel */}
        <div className="w-80 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 overflow-y-auto">
          <InspectorPanel
            stage={selectedStage || null}
            behavior={selectedBehavior || null}
            onUpdateStage={(updates) => {
              if (selectedStageId) {
                useBlueprintStore.getState().updateStage(selectedStageId, updates);
              }
            }}
            onUpdateBehavior={(updates) => {
              if (selectedStageId && selectedBehaviorId) {
                useBlueprintStore.getState().updateBehavior(selectedStageId, selectedBehaviorId, updates);
              }
            }}
          />
        </div>
      </div>

      {/* Bottom: Scoring Summary */}
      <div className="bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-6 py-3">
        <ScoringSummary stages={currentBlueprint.stages} />
      </div>

      {/* Publish Modal */}
      {showPublishModal && (
        <PublishModal
          blueprintId={currentBlueprint.id}
          onClose={() => setShowPublishModal(false)}
          onSuccess={() => {
            setShowPublishModal(false);
            loadBlueprint(currentBlueprint.id);
          }}
        />
      )}

      {/* Add Stage Dialog */}
      <AddStageDialog
        isOpen={showAddStageDialog}
        onClose={() => setShowAddStageDialog(false)}
        onSuccess={async (newBlueprintId?: string) => {
          if (newBlueprintId && (id === 'new' || currentBlueprint?.id === 'new')) {
            // Navigate to the new blueprint ID
            navigate(`/blueprints/${newBlueprintId}`, { replace: true });
          }
        }}
      />

      {/* Add Behavior Dialog */}
      {addBehaviorStageId && (
        <AddBehaviorDialog
          isOpen={showAddBehaviorDialog}
          onClose={() => {
            setShowAddBehaviorDialog(false);
            setAddBehaviorStageId(null);
          }}
          stageId={addBehaviorStageId}
          onSuccess={async (newBlueprintId?: string) => {
            if (newBlueprintId && (id === 'new' || currentBlueprint?.id === 'new')) {
              // Navigate to the new blueprint ID
              navigate(`/blueprints/${newBlueprintId}`, { replace: true });
            }
          }}
        />
      )}
    </div>
  );
}

