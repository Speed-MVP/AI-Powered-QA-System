import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface EvaluationCriteria {
  id: string
  categoryName: string
  weight: number
  passingScore: number
  evaluationPrompt: string
}

export interface PolicyTemplate {
  id: string
  name: string
  description: string
  isActive: boolean
  criteria: EvaluationCriteria[]
  createdAt: string
  updatedAt: string
}

interface PolicyState {
  templates: PolicyTemplate[]
  activeTemplate: PolicyTemplate | null
  createTemplate: (name: string, description: string) => PolicyTemplate
  updateTemplate: (id: string, updates: Partial<PolicyTemplate>) => void
  deleteTemplate: (id: string) => void
  setActiveTemplate: (id: string) => void
  addCriteria: (templateId: string, criteria: Omit<EvaluationCriteria, 'id'>) => void
  updateCriteria: (templateId: string, criteriaId: string, updates: Partial<EvaluationCriteria>) => void
  deleteCriteria: (templateId: string, criteriaId: string) => void
}

const defaultTemplate: PolicyTemplate = {
  id: 'default',
  name: 'Default QA Template',
  description: 'Standard quality assurance evaluation template',
  isActive: true,
  criteria: [
    {
      id: '1',
      categoryName: 'Compliance',
      weight: 40,
      passingScore: 90,
      evaluationPrompt: 'Evaluate if the agent followed all compliance guidelines including required disclosures, identity verification, and regulatory requirements. Score higher if all compliance protocols were met.'
    },
    {
      id: '2',
      categoryName: 'Empathy',
      weight: 30,
      passingScore: 70,
      evaluationPrompt: 'Assess how well the agent acknowledged customer emotions and concerns. Look for empathetic language, active listening indicators, and appropriate responses to customer frustration.'
    },
    {
      id: '3',
      categoryName: 'Resolution',
      weight: 30,
      passingScore: 80,
      evaluationPrompt: 'Determine if the customer\'s issue was successfully resolved. Check for customer confirmation of satisfaction, clear action plans, and follow-up commitments.'
    }
  ],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
}

export const usePolicyStore = create<PolicyState>()(
  persist(
    (set) => ({
      templates: [defaultTemplate],
      activeTemplate: defaultTemplate,
      createTemplate: (name: string, description: string) => {
          const newTemplate: PolicyTemplate = {
            id: crypto.randomUUID(),
            name,
            description,
            isActive: false,
            criteria: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }
          set((state) => ({
            templates: [...state.templates, newTemplate],
          }))
          return newTemplate
        },
        updateTemplate: (id: string, updates: Partial<PolicyTemplate>) => {
          set((state) => ({
            templates: state.templates.map((t) =>
              t.id === id ? { ...t, ...updates, updatedAt: new Date().toISOString() } : t
            ),
            activeTemplate: state.activeTemplate?.id === id 
              ? { ...state.activeTemplate, ...updates } 
              : state.activeTemplate
          }))
        },
        deleteTemplate: (id: string) => {
          set((state) => ({
            templates: state.templates.filter((t) => t.id !== id),
            activeTemplate: state.activeTemplate?.id === id ? null : state.activeTemplate
          }))
        },
        setActiveTemplate: (id: string) => {
          set((state) => ({
            templates: state.templates.map((t) => ({
              ...t,
              isActive: t.id === id
            })),
            activeTemplate: state.templates.find((t) => t.id === id) || null
          }))
        },
        addCriteria: (templateId: string, criteria: Omit<EvaluationCriteria, 'id'>) => {
          set((state) => ({
            templates: state.templates.map((t) =>
              t.id === templateId
                ? {
                    ...t,
                    criteria: [...t.criteria, { ...criteria, id: crypto.randomUUID() }],
                    updatedAt: new Date().toISOString()
                  }
                : t
            ),
            activeTemplate: state.activeTemplate?.id === templateId
              ? {
                  ...state.activeTemplate,
                  criteria: [...state.activeTemplate.criteria, { ...criteria, id: crypto.randomUUID() }]
                }
              : state.activeTemplate
          }))
        },
        updateCriteria: (templateId: string, criteriaId: string, updates: Partial<EvaluationCriteria>) => {
          set((state) => ({
            templates: state.templates.map((t) =>
              t.id === templateId
                ? {
                    ...t,
                    criteria: t.criteria.map((c) =>
                      c.id === criteriaId ? { ...c, ...updates } : c
                    ),
                    updatedAt: new Date().toISOString()
                  }
                : t
            ),
            activeTemplate: state.activeTemplate?.id === templateId
              ? {
                  ...state.activeTemplate,
                  criteria: state.activeTemplate.criteria.map((c) =>
                    c.id === criteriaId ? { ...c, ...updates } : c
                  )
                }
              : state.activeTemplate
          }))
        },
        deleteCriteria: (templateId: string, criteriaId: string) => {
          set((state) => ({
            templates: state.templates.map((t) =>
              t.id === templateId
                ? {
                    ...t,
                    criteria: t.criteria.filter((c) => c.id !== criteriaId),
                    updatedAt: new Date().toISOString()
                  }
                : t
            ),
            activeTemplate: state.activeTemplate?.id === templateId
              ? {
                  ...state.activeTemplate,
                  criteria: state.activeTemplate.criteria.filter((c) => c.id !== criteriaId)
                }
              : state.activeTemplate
          }))
        },
      }),
    {
      name: 'policy-storage',
      onRehydrateStorage: () => (state) => {
        // Ensure we have at least one template and an active one after hydration
        if (state && state.templates.length === 0) {
          state.templates = [defaultTemplate]
        }
        if (state && !state.activeTemplate) {
          state.activeTemplate = state.templates.find(t => t.isActive) || state.templates[0]
        }
      },
    }
  )
)

