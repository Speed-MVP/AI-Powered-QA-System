/**
 * Blueprint Store - Phase 8
 * Zustand store for Blueprint state management
 */

import { create } from 'zustand';
import { api } from '../lib/api';

export type BehaviorType = 'required' | 'optional' | 'forbidden' | 'critical';
export type DetectionMode = 'semantic' | 'exact_phrase' | 'hybrid';
export type CriticalAction = 'fail_stage' | 'fail_overall' | 'flag_only';

export interface Behavior {
  id: string;
  behavior_name: string;
  description?: string;
  behavior_type: BehaviorType;
  detection_mode: DetectionMode;
  phrases?: string[];
  weight: number;
  critical_action?: CriticalAction;
  ui_order: number;
  metadata?: Record<string, any>;
}

export interface Stage {
  id: string;
  stage_name: string;
  ordering_index: number;
  stage_weight?: number;
  metadata?: Record<string, any>;
  behaviors: Behavior[];
}

export interface Blueprint {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'published' | 'archived';
  version_number: number;
  compiled_flow_version_id?: string;
  created_at: string;
  updated_at: string;
  stages: Stage[];
  metadata?: Record<string, any>;
}

interface BlueprintStore {
  // State
  currentBlueprint: Blueprint | null;
  etag: string | null;
  isDirty: boolean;
  lastSavedAt: Date | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  loadBlueprint: (id: string) => Promise<void>;
  createBlueprint: (name: string, description?: string) => Promise<string>; // Returns new blueprint ID
  initializeNewBlueprint: () => void;
  saveBlueprint: () => Promise<void>;
  updateBlueprint: (updates: Partial<Blueprint>) => void;
  updateStage: (stageId: string, updates: Partial<Stage>) => void;
  updateBehavior: (stageId: string, behaviorId: string, updates: Partial<Behavior>) => void;
  addStage: (stage: Omit<Stage, 'id'>) => Promise<string | undefined>; // Returns new blueprint ID if blueprint was created
  addBehavior: (stageId: string, behavior: Omit<Behavior, 'id'>) => Promise<string | undefined>; // Returns new blueprint ID if blueprint was created
  deleteStage: (stageId: string) => Promise<void>;
  deleteBehavior: (stageId: string, behaviorId: string) => Promise<void>;
  reorderStages: (stageIds: string[]) => Promise<void>;
  reset: () => void;
}

export const useBlueprintStore = create<BlueprintStore>((set, get) => ({
  // Initial state
  currentBlueprint: null,
  etag: null,
  isDirty: false,
  lastSavedAt: null,
  isLoading: false,
  error: null,

  // Load blueprint
  loadBlueprint: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const blueprintData = await api.getBlueprint(id);
      
      // Debug: log the response structure
      console.log('Blueprint data received:', blueprintData);
      console.log('Stages data:', blueprintData.stages);
      
      // Map API response to Blueprint interface
      const blueprint: Blueprint = {
        id: String(blueprintData.id),
        name: String(blueprintData.name || ''),
        description: blueprintData.description ? String(blueprintData.description) : undefined,
        status: (blueprintData.status as 'draft' | 'published' | 'archived') || 'draft',
        version_number: Number(blueprintData.version_number) || 1,
        created_at: new Date().toISOString(), // API doesn't return this, use current time
        updated_at: new Date().toISOString(), // API doesn't return this, use current time
        stages: (blueprintData.stages || []).map((stage: any) => {
          // Ensure stage_name is a string
          const stageName = typeof stage.stage_name === 'string' 
            ? stage.stage_name 
            : (stage.stage_name?.toString() || 'Unnamed Stage');
          
          return {
            id: String(stage.id || ''),
            stage_name: stageName,
            ordering_index: Number(stage.ordering_index) || 0,
            stage_weight: stage.stage_weight !== undefined && stage.stage_weight !== null 
              ? Number(stage.stage_weight) 
              : undefined,
            metadata: stage.metadata || stage.extra_metadata || {},
            behaviors: (stage.behaviors || []).map((behavior: any) => ({
              id: String(behavior.id || ''),
              behavior_name: String(behavior.behavior_name || ''),
              behavior_type: (behavior.behavior_type as BehaviorType) || 'required',
              detection_mode: (behavior.detection_mode as DetectionMode) || 'semantic',
              weight: Number(behavior.weight) || 0,
              critical_action: behavior.critical_action as CriticalAction | undefined,
              ui_order: Number(behavior.ui_order) || 0,
              phrases: Array.isArray(behavior.phrases) ? behavior.phrases : [],
              description: behavior.description ? String(behavior.description) : undefined,
              metadata: behavior.metadata || behavior.extra_metadata || {}
            }))
          };
        }),
        metadata: (blueprintData as any).metadata || (blueprintData as any).extra_metadata || {}
      };
      
      set({
        currentBlueprint: blueprint,
        etag: null, // TODO: Get from response headers
        isDirty: false,
        lastSavedAt: new Date(),
        isLoading: false
      });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Create new blueprint
  createBlueprint: async (name: string, description?: string) => {
    set({ isLoading: true, error: null });
    try {
      // Create blueprint with empty stages array
      const blueprint = await api.createBlueprint({
        name,
        description: description || '',
        stages: []
      });
      // Reload to get full blueprint data
      const fullBlueprint = await api.getBlueprint(blueprint.id);
      set({
        currentBlueprint: fullBlueprint as Blueprint,
        etag: null, // TODO: Get from response headers
        isDirty: false,
        lastSavedAt: new Date(),
        isLoading: false
      });
      return blueprint.id;
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Save blueprint
  saveBlueprint: async () => {
    const { currentBlueprint, etag } = get();
    if (!currentBlueprint) return;
    
    // Don't save if it's a new blueprint (use createBlueprint instead)
    if (currentBlueprint.id === 'new') {
      throw new Error('Cannot save new blueprint. Use createBlueprint instead.');
    }

    set({ isLoading: true, error: null });
    try {
      // Only send fields that the backend expects for updates
      const updateData = {
        name: currentBlueprint.name,
        description: currentBlueprint.description || undefined,
        metadata: currentBlueprint.metadata || undefined,
        stages: currentBlueprint.stages.map(stage => ({
          stage_name: stage.stage_name,
          ordering_index: stage.ordering_index,
          stage_weight: stage.stage_weight,
          metadata: stage.metadata || {},
          behaviors: stage.behaviors.map(behavior => ({
            behavior_name: behavior.behavior_name,
            description: behavior.description || undefined,
            behavior_type: behavior.behavior_type,
            detection_mode: behavior.detection_mode,
            phrases: behavior.phrases || undefined,
            weight: behavior.weight,
            critical_action: behavior.critical_action || undefined,
            ui_order: behavior.ui_order || 0,
            metadata: behavior.metadata || {}
          }))
        }))
      };
      
      // Use updateBlueprint API method
      await api.updateBlueprint(
        currentBlueprint.id,
        updateData,
        etag || undefined
      );
      
      // Reload to get full updated blueprint
      const fullBlueprint = await api.getBlueprint(currentBlueprint.id);
      
      set({
        currentBlueprint: fullBlueprint as Blueprint,
        etag: null, // TODO: Get from response headers
        isDirty: false,
        lastSavedAt: new Date(),
        isLoading: false
      });
    } catch (error: any) {
      if (error.message?.includes('409') || error.message?.includes('Conflict')) {
        // Conflict - reload blueprint
        await get().loadBlueprint(currentBlueprint.id);
        set({ error: 'Blueprint was modified by another user. Please review changes.' });
      } else {
        set({ error: error.message, isLoading: false });
      }
      throw error;
    }
  },

  // Update blueprint
  updateBlueprint: (updates: Partial<Blueprint>) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    set({
      currentBlueprint: { ...currentBlueprint, ...updates },
      isDirty: true
    });
  },

  // Update stage
  updateStage: (stageId: string, updates: Partial<Stage>) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    const stages = currentBlueprint.stages.map(stage =>
      stage.id === stageId ? { ...stage, ...updates } : stage
    );

    set({
      currentBlueprint: { ...currentBlueprint, stages },
      isDirty: true
    });
  },

  // Update behavior
  updateBehavior: (stageId: string, behaviorId: string, updates: Partial<Behavior>) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    const stages = currentBlueprint.stages.map(stage => {
      if (stage.id === stageId) {
        const behaviors = stage.behaviors.map(behavior =>
          behavior.id === behaviorId ? { ...behavior, ...updates } : behavior
        );
        return { ...stage, behaviors };
      }
      return stage;
    });

    set({
      currentBlueprint: { ...currentBlueprint, stages },
      isDirty: true
    });
  },

  // Add stage
  addStage: async (stageData: Omit<Stage, 'id'>) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    // If blueprint is new, create it first
    if (currentBlueprint.id === 'new') {
      // Auto-generate name if not provided
      const blueprintName = currentBlueprint.name.trim() || 'Untitled Blueprint';
      
      // Create the blueprint first
      const newId = await get().createBlueprint(
        blueprintName,
        currentBlueprint.description
      );
      
      // Reload to get the full blueprint
      await get().loadBlueprint(newId);
      const { currentBlueprint: updatedBlueprint } = get();
      
      if (!updatedBlueprint) {
        throw new Error('Failed to load created blueprint');
      }
      
      // Now add the stage to the newly created blueprint
      try {
        await api.addStage(updatedBlueprint.id, stageData);
        await get().loadBlueprint(updatedBlueprint.id);
        // Return the new blueprint ID so the component can navigate
        return updatedBlueprint.id;
      } catch (error) {
        throw error;
      }
    }

    // Optimistic update for existing blueprint
    const newStage: Stage = {
      ...stageData,
      id: `temp-${Date.now()}`
    };

    set({
      currentBlueprint: {
        ...currentBlueprint,
        stages: [...currentBlueprint.stages, newStage]
      },
      isDirty: true
    });

    // Save to server
    try {
      await api.addStage(currentBlueprint.id, stageData);
      await get().loadBlueprint(currentBlueprint.id);
    } catch (error) {
      // Revert on error
      set({
        currentBlueprint: {
          ...currentBlueprint,
          stages: currentBlueprint.stages.filter(s => s.id !== newStage.id)
        }
      });
      throw error;
    }
  },

  // Add behavior
  addBehavior: async (stageId: string, behaviorData: Omit<Behavior, 'id'>) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    // If blueprint is new, create it first
    if (currentBlueprint.id === 'new') {
      // Auto-generate name if not provided
      const blueprintName = currentBlueprint.name.trim() || 'Untitled Blueprint';
      
      // Create the blueprint first (with the stage if it doesn't exist)
      const newId = await get().createBlueprint(
        blueprintName,
        currentBlueprint.description
      );
      
      // Reload to get the full blueprint
      await get().loadBlueprint(newId);
      const { currentBlueprint: updatedBlueprint } = get();
      
      if (!updatedBlueprint) {
        throw new Error('Failed to load created blueprint');
      }
      
      // Find the stage - if it was a temp stage, we need to find it by ordering_index
      // For now, if stage doesn't exist, we'll need to create it first
      let targetStage = updatedBlueprint.stages.find(s => s.id === stageId);
      
      // If stage not found, it might be a temp stage - create it first
      if (!targetStage && currentBlueprint.stages.length > 0) {
        const tempStage = currentBlueprint.stages.find(s => s.id === stageId);
        if (tempStage) {
          // Create the stage first
          await api.addStage(updatedBlueprint.id, {
            stage_name: tempStage.stage_name,
            ordering_index: tempStage.ordering_index,
            stage_weight: tempStage.stage_weight,
            metadata: tempStage.metadata || {}
          });
          await get().loadBlueprint(updatedBlueprint.id);
          const { currentBlueprint: reloadedBlueprint } = get();
          targetStage = reloadedBlueprint?.stages.find(s => 
            s.stage_name === tempStage.stage_name && 
            s.ordering_index === tempStage.ordering_index
          );
        }
      }
      
      if (!targetStage) {
        throw new Error('Stage not found after creating blueprint');
      }
      
      // Now add the behavior to the newly created blueprint
      try {
        await api.addBehavior(updatedBlueprint.id, targetStage.id, behaviorData);
        await get().loadBlueprint(updatedBlueprint.id);
        // Return the new blueprint ID so the component can navigate
        return updatedBlueprint.id;
      } catch (error) {
        throw error;
      }
    }

    // Optimistic update for existing blueprint
    const newBehavior: Behavior = {
      ...behaviorData,
      id: `temp-${Date.now()}`
    };

    const stages = currentBlueprint.stages.map(stage => {
      if (stage.id === stageId) {
        return { ...stage, behaviors: [...stage.behaviors, newBehavior] };
      }
      return stage;
    });

    set({
      currentBlueprint: { ...currentBlueprint, stages },
      isDirty: true
    });

    // Save to server
    try {
      await api.addBehavior(currentBlueprint.id, stageId, behaviorData);
      await get().loadBlueprint(currentBlueprint.id);
    } catch (error) {
      // Revert on error
      set({ currentBlueprint });
      throw error;
    }
  },

  // Delete stage
  deleteStage: async (stageId: string) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    try {
      await api.deleteBlueprintStage(currentBlueprint.id, stageId);
      await get().loadBlueprint(currentBlueprint.id);
    } catch (error) {
      throw error;
    }
  },

  // Delete behavior
  deleteBehavior: async (stageId: string, behaviorId: string) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    try {
      await api.deleteBehavior(currentBlueprint.id, stageId, behaviorId);
      await get().loadBlueprint(currentBlueprint.id);
    } catch (error) {
      throw error;
    }
  },

  // Reorder stages
  reorderStages: async (stageIds: string[]) => {
    const { currentBlueprint } = get();
    if (!currentBlueprint) return;

    // Optimistic update
    const stagesMap = new Map(currentBlueprint.stages.map(s => [s.id, s]));
    const reorderedStages = stageIds
      .map((id, index) => ({
        ...stagesMap.get(id)!,
        ordering_index: index + 1
      }))
      .filter(Boolean);

    set({
      currentBlueprint: { ...currentBlueprint, stages: reorderedStages },
      isDirty: true
    });

    // Save to server
    try {
      await get().saveBlueprint();
    } catch (error) {
      // Revert on error
      await get().loadBlueprint(currentBlueprint.id);
      throw error;
    }
  },

  // Initialize new blueprint (for "new" route)
  initializeNewBlueprint: () => {
    const newBlueprint: Blueprint = {
      id: 'new',
      name: '',
      description: '',
      status: 'draft',
      version_number: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      stages: [],
      metadata: {}
    };
    set({
      currentBlueprint: newBlueprint,
      etag: null,
      isDirty: false,
      lastSavedAt: null,
      error: null
    });
  },

  // Reset store
  reset: () => {
    set({
      currentBlueprint: null,
      etag: null,
      isDirty: false,
      lastSavedAt: null,
      error: null
    });
  }
}));

