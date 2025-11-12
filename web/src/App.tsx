import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Test } from '@/pages/Test'
import { Home } from '@/pages/Home'
import { Dashboard } from '@/pages/Dashboard'
import { Results } from '@/pages/Results'
import { PolicyTemplates } from '@/pages/PolicyTemplates'
import { HumanReview } from '@/pages/HumanReview'
import { Pricing } from '@/pages/Pricing'
import { Features } from '@/pages/Features'
import { FAQ } from '@/pages/FAQ'
import { SignIn } from '@/pages/SignIn'
import { TeamsListPage } from '@/pages/TeamsListPage'
import { AgentsListPage } from '@/pages/AgentsListPage'
import { AuditTrailPage } from '@/pages/AuditTrailPage'
import { SupervisorDashboard } from '@/pages/SupervisorDashboard'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { useSEO, pageSEO } from '@/hooks/useSEO'

// SEO Wrapper Component
function SEOWrapper({ children, seoConfig }: { children: React.ReactNode, seoConfig: any }) {
  useSEO(seoConfig)
  return <>{children}</>
}

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
        <Route
          path="sign-in"
          element={
            <SEOWrapper seoConfig={pageSEO.signIn}>
              <SignIn />
            </SEOWrapper>
          }
        />
        <Route
          path="login"
          element={
            <SEOWrapper seoConfig={pageSEO.signIn}>
              <SignIn />
            </SEOWrapper>
          }
        />
        <Route
          index
          element={
            <SEOWrapper seoConfig={pageSEO.home}>
              <Home />
            </SEOWrapper>
          }
        />
        <Route
          path="demo"
          element={
            <SEOWrapper seoConfig={pageSEO.demo}>
              <ProtectedRoute>
                <Test />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="home"
          element={
            <SEOWrapper seoConfig={pageSEO.home}>
              <Home />
            </SEOWrapper>
          }
        />
        <Route
          path="dashboard"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="results/:recordingId"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="policy-templates"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <PolicyTemplates />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="human-review"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <HumanReview />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="teams"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <TeamsListPage />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="agents"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <AgentsListPage />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="audit-log"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <AuditTrailPage />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="supervisor"
          element={
            <SEOWrapper seoConfig={pageSEO.dashboard}>
              <ProtectedRoute>
                <SupervisorDashboard />
              </ProtectedRoute>
            </SEOWrapper>
          }
        />
        <Route
          path="pricing"
          element={
            <SEOWrapper seoConfig={pageSEO.pricing}>
              <Pricing />
            </SEOWrapper>
          }
        />
        <Route
          path="features"
          element={
            <SEOWrapper seoConfig={pageSEO.features}>
              <Features />
            </SEOWrapper>
          }
        />
        <Route
          path="faq"
          element={
            <SEOWrapper seoConfig={pageSEO.faq}>
              <FAQ />
            </SEOWrapper>
          }
        />
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
