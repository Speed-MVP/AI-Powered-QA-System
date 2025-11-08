export function SignIn() {
  return (
    <div className="min-h-screen relative flex items-center justify-center">
      {/* Subtle background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-400/10 dark:bg-brand-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/8 dark:bg-purple-500/3 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
      </div>
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12 relative w-full">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
          Sign In
        </h1>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <p className="text-gray-600 dark:text-gray-400 text-center">
            Sign in functionality will be implemented here.
          </p>
        </div>
      </div>
    </div>
  )
}

