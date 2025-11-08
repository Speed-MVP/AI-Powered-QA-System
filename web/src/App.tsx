import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Test } from '@/pages/Test'
import { Home } from '@/pages/Home'
import { Dashboard } from '@/pages/Dashboard'
import { Results } from '@/pages/Results'
import { PolicyTemplates } from '@/pages/PolicyTemplates'
import { Pricing } from '@/pages/Pricing'
import { Features } from '@/pages/Features'
import { FAQ } from '@/pages/FAQ'
import { SignIn } from '@/pages/SignIn'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route path="sign-in" element={<SignIn />} />
        <Route path="login" element={<SignIn />} />
        <Route
          index
          element={
            <ProtectedRoute>
              <Test />
            </ProtectedRoute>
          }
        />
        <Route
          path="test"
          element={
            <ProtectedRoute>
              <Test />
            </ProtectedRoute>
          }
        />
        <Route path="home" element={<Home />} />
        <Route
          path="dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="results"
          element={
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          }
        />
        <Route
          path="policy-templates"
          element={
            <ProtectedRoute>
              <PolicyTemplates />
            </ProtectedRoute>
          }
        />
        <Route path="pricing" element={<Pricing />} />
        <Route path="features" element={<Features />} />
        <Route path="faq" element={<FAQ />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
