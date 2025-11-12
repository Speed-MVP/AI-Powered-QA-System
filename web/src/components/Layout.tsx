import { Link, Outlet } from 'react-router-dom'
import { useThemeStore } from '@/store/themeStore'
import { useAuth } from '@/contexts/AuthContext'
import { Sun, Moon, LogOut, User } from 'lucide-react'
import { useEffect } from 'react'
import { Footer } from './Footer'
import { FloatingButtons } from './FloatingButtons'

export function Layout() {
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)
  const { isAuthenticated, user, logout } = useAuth()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="min-h-screen bg-white dark:bg-[#0A0F1A] flex flex-col">
      <nav className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-[#0A0F1A]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center flex-shrink-0">
              <Link to="/" className="flex items-center space-x-3">
                <img
                  src="/Logo.svg"
                  alt="Qualitidex"
                  className="h-8 w-auto"
                  loading="lazy"
                  decoding="async"
                />
                <span className="font-semibold text-gray-900 dark:text-white text-lg">
                  Qualitidex
                </span>
              </Link>
            </div>

            <div className="hidden md:flex items-center justify-center flex-1 space-x-8">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/dashboard"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/supervisor"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Supervisor
                  </Link>
                  <Link
                    to="/human-review"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Human Review
                  </Link>
                  <Link
                    to="/policy-templates"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Templates
                  </Link>
                  <Link
                    to="/teams"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Teams
                  </Link>
                  <Link
                    to="/agents"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Agents
                  </Link>
                  <Link
                    to="/audit-log"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Audit
                  </Link>
                  <Link
                    to="/test"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Test
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/home"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Home
                  </Link>
                  <Link
                    to="/test"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Test
                  </Link>
                  <Link
                    to="/pricing"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Pricing
                  </Link>
                  <Link
                    to="/features"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    Features
                  </Link>
                  <Link
                    to="/faq"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                  >
                    FAQ
                  </Link>
                </>
              )}
            </div>

            <div className="flex items-center space-x-3 flex-shrink-0">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Toggle theme"
                type="button"
              >
                {theme === 'dark' ? (
                  <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                )}
              </button>

              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <User className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {user?.email || 'User'}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-semibold shadow-sm hover:shadow-md flex items-center space-x-2"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              ) : (
                <Link
                  to="/sign-in"
                  className="px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors text-sm font-semibold shadow-sm hover:shadow-md"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>

          <div className="md:hidden flex justify-center items-center space-x-6 pb-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/supervisor"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Supervisor
                </Link>
                <Link
                  to="/human-review"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Review
                </Link>
                <Link
                  to="/policy-templates"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Templates
                </Link>
                <Link
                  to="/teams"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Teams
                </Link>
                <Link
                  to="/agents"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Agents
                </Link>
                <Link
                  to="/audit-log"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Audit
                </Link>
                <Link
                  to="/test"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Test
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/home"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Home
                </Link>
                <Link
                  to="/test"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Test
                </Link>
                <Link
                  to="/pricing"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Pricing
                </Link>
                <Link
                  to="/features"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  Features
                </Link>
                <Link
                  to="/faq"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm font-medium"
                >
                  FAQ
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="flex-1">
        <Outlet />
      </main>

      <Footer />
      <FloatingButtons />
    </div>
  )
}

