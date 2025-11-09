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
            Enterprise AI QA Pricing
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Reduce BPO QA staffing by 80-90% while achieving 100% call coverage. Enterprise AI that scales with your operations.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Philippine BPO-focused pricing | Replace 10-15 QA staff with AI + 2-3 specialists
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* PH BPO Starter Plan */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-gray-200 dark:border-gray-700 p-8 hover:border-brand-500 dark:hover:border-brand-500 transition-colors duration-200 shadow-sm hover:shadow-lg flex flex-col h-full">
          <div className="flex-1">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">PH BPO Starter</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                Perfect for small BPO operations | Reduce QA hiring costs by 70%
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">₱25,000</span>
                <span className="text-gray-600 dark:text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                ₱8.33 per call processed | Save ₱15,000-25,000 monthly vs QA salaries
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3">
                  <FaChartLine className="text-blue-600 dark:text-blue-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">3,000 calls</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Monthly processing included</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                ~90 hours of audio | Perfect for 15-25 agent operations
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Overage: ₱7/call | Setup fee: ₱8,000 (ROI in 1 month)
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Nova-2 ASR + Forced Alignment</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Gemini Flash/Pro Hybrid Intelligence</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">8-Class Emotion Analysis + Adaptive Baselines</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">RAG-Powered Policy Retrieval</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Ensemble Scoring + Confidence Routing</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Continuous Learning & Fine-Tuning</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Supervisor Dashboard & Analytics</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Batch Processing & API Access</span>
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

        {/* BPO Enterprise Plan - Popular */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-brand-500 p-8 shadow-lg relative flex flex-col h-full">
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <span className="bg-brand-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
              BPO MOST POPULAR
            </span>
          </div>

          <div className="flex-1">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">PH BPO Enterprise</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                For established BPO operations | Replace 50-80 QA staff with AI + 8-10 specialists
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">₱120,000</span>
                <span className="text-gray-600 dark:text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                ₱2.50 per call processed | Save ₱600,000-1,200,000 monthly vs QA salaries
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center mr-3">
                  <FaRocket className="text-brand-600 dark:text-brand-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">48,000 calls</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Monthly processing included</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                ~1,440 hours of audio | Perfect for 300-500 agent operations
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Overage: ₱2/call | Setup fee: ₱30,000 (ROI in 1-2 months)
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Everything in Professional</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Unlimited Batch Processing</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Advanced Compliance & Audit</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Custom Model Fine-Tuning</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Dedicated Account Management</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">24/7 Priority Support</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Custom Integrations</span>
              </li>
              <li className="flex items-start">
                <FaCheck className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-600 dark:text-gray-400">SLA: 99.9% uptime</span>
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

        {/* BPO Global Plan */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-gray-300 dark:border-gray-600 p-8 hover:border-brand-500 dark:hover:border-brand-500 transition-colors duration-200 shadow-sm hover:shadow-lg flex flex-col h-full">
          <div className="flex-1">
            <div className="mb-6">
              <div className="flex items-center mb-2">
                <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3">
                  <FaUsers className="text-purple-600 dark:text-purple-400 text-xl" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">BPO Global</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                For large BPO operations (50,000+ calls/month)
              </p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-gray-900 dark:text-white">Custom</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Volume pricing from $15,000/month
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3">
                  <FaChartLine className="text-purple-600 dark:text-purple-400 text-xl" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">Unlimited</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Processing capacity</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Scale to millions of calls across multiple sites
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Multi-site deployment, custom integrations
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

        {/* BPO Staffing Reduction Calculator */}
        <div className="mb-16 bg-gradient-to-r from-blue-600 to-brand-600 rounded-xl p-8 text-white">
          <h2 className="text-3xl font-bold mb-6 text-center">
            Reduce QA Staffing Costs by 80-90%
          </h2>

          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4">Traditional BPO QA</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>QA Team Size:</span>
                  <span className="font-bold">10-15 people</span>
                </div>
                <div className="flex justify-between">
                  <span>Monthly Cost:</span>
                  <span className="font-bold">$7,000-12,000</span>
                </div>
                <div className="flex justify-between">
                  <span>Calls Reviewed:</span>
                  <span className="font-bold">1-3% sample</span>
                </div>
                <div className="flex justify-between">
                  <span>Turnover Impact:</span>
                  <span className="font-bold">High</span>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4">AI QA Solution</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>QA Team Size:</span>
                  <span className="font-bold">2-3 people</span>
                </div>
                <div className="flex justify-between">
                  <span>Monthly Cost:</span>
                  <span className="font-bold">$1,299-6,499</span>
                </div>
                <div className="flex justify-between">
                  <span>Calls Reviewed:</span>
                  <span className="font-bold">100% coverage</span>
                </div>
                <div className="flex justify-between">
                  <span>Turnover Impact:</span>
                  <span className="font-bold">Minimal</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className="text-4xl font-bold mb-2">$5,700-10,500 Monthly Savings</div>
            <div className="text-xl opacity-90">Payback in 1-2 months</div>
            <div className="mt-4 text-sm opacity-80">
              Based on Philippine BPO average salaries (₱20,000-35,000/month per QA specialist)
            </div>
          </div>
        </div>

        {/* PH BPO ROI Calculator */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-8">
            Philippine BPO ROI Calculator
          </h2>
          <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl p-8 border border-green-200 dark:border-green-800">
            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">₱35,000</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Average QA Salary (monthly)</div>
                <div className="text-xs text-gray-500 mt-1">Including benefits & training</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">₱6.23</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">AI QA Cost per Call</div>
                <div className="text-xs text-gray-500 mt-1">Enterprise plan pricing</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">80%</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">QA Staff Reduction</div>
                <div className="text-xs text-gray-500 mt-1">Keep 20% for complex cases</div>
              </div>
            </div>

            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">
                Sample ROI: 300-Agent BPO Center
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Current Manual QA:</h4>
                  <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                    <li>• 24 QA staff needed (8% ratio)</li>
                    <li>• ₱840,000 monthly QA cost</li>
                    <li>• 3-5% call sampling only</li>
                    <li>• Inconsistent quality</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-green-700 dark:text-green-300 mb-3">With AI QA System:</h4>
                  <ul className="space-y-2 text-sm text-green-700 dark:text-green-300">
                    <li>• 5 QA specialists needed</li>
                    <li>• ₱299,000 monthly cost</li>
                    <li>• 100% call coverage</li>
                    <li>• Consistent, improving quality</li>
                  </ul>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-2">
                    ₱545,000 Monthly Savings
                  </div>
                  <div className="text-lg text-gray-600 dark:text-gray-400">
                    65% cost reduction • ROI in 1-2 months • 33x more calls reviewed
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enterprise Features Included */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-8">
            Enterprise-Grade Platform
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <FaShieldAlt className="text-blue-600 dark:text-blue-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Regulatory Compliance</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                GDPR, HIPAA, SOX compliant with comprehensive audit trails and version control
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                <FaRocket className="text-green-600 dark:text-green-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Scalable Architecture</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Batch processing of 1000+ recordings simultaneously with intelligent queue management
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-4">
                <FaCog className="text-purple-600 dark:text-purple-400 text-xl" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Self-Learning AI</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Continuous model improvement through weekly fine-tuning with your quality data
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
              Pricing is based on monthly call volume. Each plan includes a set number of calls processed per month. Additional calls are charged at the overage rate. This provides predictable costs and scales with your business.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              How does this reduce BPO staffing needs?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Traditional BPO QA requires 10-15 people per 10,000 calls/month for 1-3% sampling. Our AI handles 95% of evaluations automatically, reducing your QA team to 2-3 people for edge cases and oversight. You'll maintain quality while cutting staffing costs by 80-90%.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              What about Philippine labor laws and turnover?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Philippine BPO turnover averages 30-50% annually. Our AI solution reduces dependency on manual QA staff, eliminating recruitment costs, training time, and quality inconsistency from high turnover. Deploy once, benefit continuously.
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

      {/* BPO ROI Calculator CTA */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <div className="bg-gradient-to-r from-green-600 to-brand-600 rounded-xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            Transform Your Philippine BPO QA Process
          </h2>
          <p className="text-xl mb-4 opacity-90">
            Replace expensive manual QA with AI that works 24/7 at ₱2.50 per call
          </p>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8 inline-block">
            <div className="grid grid-cols-2 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold mb-1">₱840,000</div>
                <div className="text-sm opacity-90">Monthly QA cost (24 staff)</div>
              </div>
              <div>
                <div className="text-3xl font-bold mb-1">₱120,000</div>
                <div className="text-sm opacity-90">AI QA cost (48K calls)</div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-white/20">
              <div className="text-2xl font-bold text-yellow-300">₱545,000 Monthly Savings</div>
              <div className="text-sm opacity-90">65% cost reduction • ROI in 1-2 months • 33x more calls reviewed</div>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/sign-in"
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-brand-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Start Free Trial
              <FaArrowRight className="ml-2 w-5 h-5" />
            </Link>
            <a
              href="mailto:sales@qasystem.com?subject=ROI Analysis Request"
              className="inline-flex items-center justify-center px-8 py-3 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition-colors"
            >
              Get Custom ROI Report
              <FaHeadset className="ml-2 w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

