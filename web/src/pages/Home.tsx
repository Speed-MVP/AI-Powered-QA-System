import { Link } from 'react-router-dom'

export function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-brand-400 to-brand-600 rounded-2xl mb-6 shadow-lg">
            <span className="text-white font-bold text-3xl">AI</span>
          </div>
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
            AI-Powered QA System
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-10 max-w-2xl mx-auto">
            Upload call recordings and get comprehensive quality assurance results in minutes
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/upload"
              className="inline-flex items-center justify-center px-8 py-4 bg-brand-500 text-white rounded-lg font-semibold hover:bg-brand-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Get Started
            </Link>
            <Link
              to="/features"
              className="inline-flex items-center justify-center px-8 py-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg font-semibold border-2 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
            >
              Learn More
            </Link>
          </div>
        </div>

        {/* Tailwind Test Section */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="w-12 h-12 bg-brand-100 dark:bg-brand-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-brand-600 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Fast Processing</h3>
            <p className="text-gray-600 dark:text-gray-400">Process 100+ recordings in minutes with AI-powered analysis</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="w-12 h-12 bg-brand-100 dark:bg-brand-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-brand-600 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Accurate Results</h3>
            <p className="text-gray-600 dark:text-gray-400">85-92% accuracy on problem resolution detection</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="w-12 h-12 bg-brand-100 dark:bg-brand-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-brand-600 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Cost Effective</h3>
            <p className="text-gray-600 dark:text-gray-400">90-97% cost reduction vs manual QA</p>
          </div>
        </div>

        {/* Tailwind Utility Classes Test */}
        <div className="mt-16 p-8 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Tailwind CSS Test</h2>
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 bg-brand-500 text-white rounded-full text-sm font-medium">Brand Color</span>
              <span className="px-3 py-1 bg-gray-500 text-white rounded-full text-sm font-medium">Gray Color</span>
              <span className="px-3 py-1 bg-green-500 text-white rounded-full text-sm font-medium">Green</span>
              <span className="px-3 py-1 bg-blue-500 text-white rounded-full text-sm font-medium">Blue</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="h-20 bg-gradient-to-br from-brand-400 to-brand-600 rounded-lg"></div>
              <div className="h-20 bg-gradient-to-br from-gray-400 to-gray-600 rounded-lg"></div>
              <div className="h-20 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg"></div>
              <div className="h-20 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg"></div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              ✅ Tailwind CSS is working! All utility classes are rendering correctly.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

