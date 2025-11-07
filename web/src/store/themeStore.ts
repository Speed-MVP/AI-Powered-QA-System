import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
}

const getInitialTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light'
  
  try {
    const stored = localStorage.getItem('theme-storage')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed?.state?.theme === 'dark' || parsed?.state?.theme === 'light') {
        return parsed.state.theme
      }
    }
  } catch {
    // Ignore parse errors
  }
  
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: getInitialTheme(),
      toggleTheme: () => {
        set((state) => ({
          theme: state.theme === 'dark' ? 'light' : 'dark',
        }))
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)

