import { Link } from 'react-router-dom'
import { 
  FaCheck, 
  FaTimes, 
  FaArrowRight, 
  FaHeadset, 
  FaShieldAlt, 
  FaRocket,
  FaChartLine,
  FaUsers,
  FaCog,
  FaEnvelope
} from 'react-icons/fa'

export function Pricing() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Subtle background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -right-20 w-96 h-96 bg-brand-400/10 dark:bg-brand-500/5 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-0 w-96 h-96 bg-green-400/8 dark:bg-green-500/3 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-400/8 dark:bg-blue-500/3 rounded-full blur-3xl"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 relative">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-3">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Choose the perfect plan for your call center. All plans include AI-powered transcription, evaluation, and comprehensive analytics.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Pricing based on hours of audio processed per month
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Starter Plan */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-gray-200 dark:border-gray-700 p-8 hover:border-brand-500 dark:hover:border-brand-500 transition-colors duration-200 shadow-sm hover:shadow-lg flex flex-col h-full">
          <div className="flex-1">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Starter</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                Perfect for small teams getting started
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">$149</span>
                <span className="text-gray-600 dark:text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                $14.90 per hour processed
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3">
                  <FaChartLine className="text-blue-600 dark:text-blue-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">10 hours</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Audio processing included</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                ~200 calls/month (avg 3 min/call)
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Overage: $12/hour for additional processing
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">AI transcription & diarization</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">LLM-powered evaluation</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Real-time dashboard</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Policy template management</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Basic analytics & reports</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Email support</span>
              </li>
              <li className="flex items-start">
                <FaTimes className="w-5 h-5 text-gray-300 dark:text-gray-700 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-400 dark:text-gray-600 line-through">Priority support</span>
              </li>
              <li className="flex items-start">
                <FaTimes className="w-5 h-5 text-gray-300 dark:text-gray-700 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-400 dark:text-gray-600 line-through">Custom integrations</span>
              </li>
            </ul>
          </div>

          <Link
            to="/sign-in"
            className="block w-full text-center px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium mt-auto"
          >
            Get Started
          </Link>
        </div>

        {/* Professional Plan - Popular */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-brand-500 p-8 shadow-lg relative flex flex-col h-full">
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <span className="bg-brand-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
              MOST POPULAR
            </span>
          </div>

          <div className="flex-1">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Professional</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                Ideal for growing call centers
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">$899</span>
                <span className="text-gray-600 dark:text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                $8.99 per hour processed
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center mr-3">
                  <FaRocket className="text-brand-600 dark:text-brand-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">100 hours</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Audio processing included</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                ~2,000 calls/month (avg 3 min/call)
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Overage: $10/hour for additional processing
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Everything in Starter</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Advanced analytics & insights</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">CSV & PDF exports</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Priority support</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Custom policy templates</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">API access</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Multi-user collaboration</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">SLA: 99.5% uptime</span>
              </li>
            </ul>
          </div>

          <Link
            to="/sign-in"
            className="block w-full text-center px-6 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors font-medium mt-auto"
          >
            Get Started
            <FaArrowRight className="inline-block ml-2 w-4 h-4" />
          </Link>
        </div>

        {/* Enterprise Plan */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-gray-300 dark:border-gray-600 p-8 hover:border-brand-500 dark:hover:border-brand-500 transition-colors duration-200 shadow-sm hover:shadow-lg flex flex-col h-full">
          <div className="flex-1">
            <div className="mb-6">
              <div className="flex items-center mb-2">
                <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3">
                  <FaUsers className="text-purple-600 dark:text-purple-400 text-xl" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">Enterprise</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                For large organizations with custom needs
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">Custom</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Volume discounts available
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3">
                  <FaChartLine className="text-purple-600 dark:text-purple-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">Unlimited</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Audio processing</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Scale to millions of calls
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Custom pricing based on volume
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Everything in Professional</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Dedicated account manager</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">24/7 priority support</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Custom integrations</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">On-premise deployment option</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">SLA: 99.9% uptime</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Advanced security & compliance</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Training & onboarding</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Custom reporting & analytics</span>
              </li>
            </ul>
          </div>

          <a
            href="mailto:sales@qasystem.com?subject=Enterprise Inquiry"
            className="block w-full text-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium mt-auto"
          >
            Contact Sales
            <FaEnvelope className="inline-block ml-2 w-4 h-4" />
          </a>
        </div>
        </div>

        {/* Features Comparison */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-8">
            All Plans Include
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <FaShieldAlt className="text-blue-600 dark:text-blue-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Enterprise Security</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                End-to-end encryption, SOC 2 compliance, and regular security audits
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                <FaRocket className="text-green-600 dark:text-green-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">High Performance</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Process 100+ recordings in parallel with sub-10 minute batch processing
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-4">
                <FaCog className="text-purple-600 dark:text-purple-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Custom Policies</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Create unlimited custom evaluation criteria tailored to your business
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-8">
          Frequently Asked Questions
        </h2>
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              How is pricing calculated?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Pricing is based on the total hours of audio processed each month. Each plan includes a set number of hours, with additional hours charged at the overage rate. Unused hours do not roll over to the next month.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              What counts as "processing"?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Processing includes transcription, speaker diarization, LLM evaluation, scoring, and analytics generation. The time is calculated based on the actual duration of your audio files.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Can I change plans later?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate any charges or credits.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              What payment methods do you accept?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              We accept all major credit cards, ACH transfers, and can arrange invoicing for Enterprise customers. All plans are billed monthly.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Is there a free trial?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Yes! All new accounts get a 14-day free trial with 2 hours of audio processing included. No credit card required.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <div className="bg-gradient-to-r from-brand-500 to-brand-600 rounded-xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            Ready to transform your QA process?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Start your free trial today. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/sign-in"
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-brand-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Start Free Trial
              <FaArrowRight className="ml-2 w-5 h-5" />
            </Link>
            <a
              href="mailto:sales@qasystem.com?subject=Pricing Inquiry"
              className="inline-flex items-center justify-center px-8 py-3 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition-colors"
            >
              Contact Sales
              <FaHeadset className="ml-2 w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

