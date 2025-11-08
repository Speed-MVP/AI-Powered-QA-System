import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/api'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  company_id: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication status on mount
  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setUser(null)
        setIsLoading(false)
        return
      }

      // Verify token by fetching current user
      const userData = await api.getCurrentUser()
      setUser(userData)
      setIsLoading(false)
    } catch (error) {
      // Token is invalid or expired
      localStorage.removeItem('auth_token')
      api.setToken(null)
      setUser(null)
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    await api.login(email, password)
    await checkAuth() // Refresh user data after login
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    api.setToken(null)
    setUser(null)
    // Navigation will be handled by ProtectedRoute component
    window.location.href = '/sign-in'
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

