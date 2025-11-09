import { 
  FaShieldAlt, 
  FaUserShield, 
  FaBuilding, 
  FaCloudUploadAlt, 
  FaChartLine, 
  FaCogs, 
  FaChartBar, 
  FaFileAlt, 
  FaBell, 
  FaEnvelope, 
  FaMobileAlt, 
  FaLock, 
  FaKey, 
  FaShieldVirus, 
  FaHistory, 
  FaTachometerAlt, 
  FaServer, 
  FaDatabase, 
  FaReact, 
  FaBrain 
} from 'react-icons/fa'
import { 
  HiOutlineDocumentText, 
  HiOutlineSparkles 
} from 'react-icons/hi'

export function Features() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Enhanced background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Large ambient lights */}
        <div className="absolute top-0 -left-40 w-[800px] h-[800px] bg-brand-400/10 dark:bg-brand-500/5 rounded-full blur-[120px]"></div>
        <div className="absolute top-1/3 -right-40 w-[700px] h-[700px] bg-purple-400/9 dark:bg-purple-500/4 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-blue-400/8 dark:bg-blue-500/4 rounded-full blur-[90px]"></div>
        
        {/* Medium accent lights */}
        <div className="absolute top-1/2 right-1/4 w-[500px] h-[500px] bg-indigo-400/6 dark:bg-indigo-500/3 rounded-full blur-[80px]"></div>
        <div className="absolute bottom-1/4 right-0 w-96 h-96 bg-pink-400/5 dark:bg-pink-500/2 rounded-full blur-3xl"></div>
        
        {/* Small highlight lights */}
        <div className="absolute top-1/4 left-1/2 w-64 h-64 bg-cyan-400/4 dark:bg-cyan-500/2 rounded-full blur-2xl"></div>
        <div className="absolute bottom-1/3 left-1/3 w-48 h-48 bg-emerald-400/3 dark:bg-emerald-500/1.5 rounded-full blur-xl"></div>
        
        {/* Gradient overlays for depth */}
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-purple-50/5 to-transparent dark:via-purple-900/5"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(139,92,246,0.08),transparent_60%)] dark:bg-[radial-gradient(ellipse_at_bottom_left,rgba(139,92,246,0.04),transparent_60%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.06),transparent_50%)] dark:bg-[radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.03),transparent_50%)]"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 relative">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4 tracking-tight">
          AI-Powered Quality Assurance Platform
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
          Transform your call center QA process with AI-powered evaluation, comprehensive analytics, and real-time insights.
        </p>
      </div>

      {/* Core Value Proposition */}
      <div className="grid md:grid-cols-3 gap-8 mb-20">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20 rounded-xl p-8 border border-blue-200 dark:border-blue-800/50 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-lg bg-blue-600 dark:bg-blue-500 flex items-center justify-center">
              <FaChartLine className="text-white text-xl" />
            </div>
            <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">90-97%</div>
          </div>
          <div className="text-gray-800 dark:text-gray-200 font-semibold text-lg mb-2">Cost Reduction</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">$0.50-2 per call vs $15-25 manual QA</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/20 rounded-xl p-8 border border-green-200 dark:border-green-800/50 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-lg bg-green-600 dark:bg-green-500 flex items-center justify-center">
              <FaChartBar className="text-white text-xl" />
            </div>
            <div className="text-4xl font-bold text-green-600 dark:text-green-400">95%</div>
          </div>
          <div className="text-gray-800 dark:text-gray-200 font-semibold text-lg mb-2">Automation Rate</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">100% call coverage, 5% human review</div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/20 rounded-xl p-8 border border-purple-200 dark:border-purple-800/50 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-lg bg-purple-600 dark:bg-purple-500 flex items-center justify-center">
              <FaTachometerAlt className="text-white text-xl" />
            </div>
            <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">Self-Learning</div>
          </div>
          <div className="text-gray-800 dark:text-gray-200 font-semibold text-lg mb-2">Continuous Improvement</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Fine-tuned models, weekly retraining</div>
        </div>
      </div>

      {/* Main Features */}
      <div className="space-y-16">
        {/* Authentication & User Management */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
              <FaShieldAlt className="text-indigo-600 dark:text-indigo-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Authentication & User Management
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-4">
                <FaKey className="text-indigo-600 dark:text-indigo-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Secure Authentication</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                Sign up, log in, and reset passwords via Supabase Auth with email verification for new accounts.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-4">
                <FaUserShield className="text-indigo-600 dark:text-indigo-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Role-Based Access</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                Three roles: Admin (full access), QA Manager (manage templates, view results), Reviewer (view results only).
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-4">
                <FaBuilding className="text-indigo-600 dark:text-indigo-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Multi-Tenant Architecture</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                Users associated with companies. Row Level Security enforces complete data isolation between organizations.
              </p>
            </div>
          </div>
        </section>

        {/* Recording Upload */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <FaCloudUploadAlt className="text-blue-600 dark:text-blue-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Recording Upload
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <FaCloudUploadAlt className="text-blue-600 dark:text-blue-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Drag & Drop Interface</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 leading-relaxed">
                Intuitive file upload with drag-and-drop or browse file selector.
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
                  <span>Supported formats: MP3, WAV, M4A, MP4</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
                  <span>Batch upload: 1-100+ files per session</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
                  <span>Max file size: 2GB per file</span>
                </li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <FaChartLine className="text-blue-600 dark:text-blue-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Progress Tracking</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 leading-relaxed">
                Real-time upload progress with percentage tracking and status updates.
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Files stored securely in Supabase Storage with CDN-backed delivery and signed URLs for secure retrieval.
              </p>
            </div>
          </div>
        </section>

        {/* Advanced AI Processing Pipeline */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <FaCogs className="text-purple-600 dark:text-purple-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Enterprise AI Processing Pipeline
            </h2>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
            <p className="text-gray-600 dark:text-gray-400 mb-8 text-lg leading-relaxed">
              Advanced multi-stage AI pipeline with hybrid models, forced alignment, and continuous learning:
            </p>
            <div className="space-y-6">
              <div className="flex items-start gap-6 p-5 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-600 dark:bg-blue-500 flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">1</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Nova-2 ASR + Forced Alignment</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    Deepgram Nova-2 transcription with diarization, followed by WhisperX forced alignment for precise word-level timestamps. Eliminates tone mismatch errors.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-6 p-5 rounded-lg bg-green-50 dark:bg-green-900/10 border border-green-100 dark:border-green-800/30">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-green-600 dark:bg-green-500 flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">2</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">8-Class Emotion Analysis</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    Local emotion classifier (anger, frustration, calm, etc.) with adaptive baselines per session. Prevents mislabeling intense agents as angry.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-6 p-5 rounded-lg bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-800/30">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-purple-600 dark:bg-purple-500 flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">3</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Hybrid Gemini Flash/Pro + RAG</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    Intelligent routing: Flash for routine calls (~70%), Pro for complex cases (~30%). Vector RAG retrieves relevant policy snippets for context-aware evaluation.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-6 p-5 rounded-lg bg-orange-50 dark:bg-orange-900/10 border border-orange-100 dark:border-orange-800/30">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-orange-600 dark:bg-orange-500 flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">4</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Ensemble Scoring + Confidence Routing</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    Weighted fusion of LLM, rules engine, and emotion scores. Confidence-based routing: {'>'}75% auto-approve, {'<'}75% human review, critical violations always reviewed.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-6 p-5 rounded-lg bg-indigo-50 dark:bg-indigo-900/10 border border-indigo-100 dark:border-indigo-800/30">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-indigo-600 dark:bg-indigo-500 flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">5</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Continuous Learning Loop</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    Weekly retraining with human-reviewed calls. Fine-tuned Gemini models with performance tracking and automatic confidence threshold calibration.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Supervisor Dashboard & Analytics */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center">
              <FaChartBar className="text-teal-600 dark:text-teal-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Supervisor Dashboard & Analytics
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-teal-300 dark:hover:border-teal-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center mb-4">
                <FaChartBar className="text-teal-600 dark:text-teal-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Advanced Analytics Dashboard</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Real-time QA performance metrics and trends</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Model usage statistics (Flash vs Pro routing)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Top policy violations and common issues</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Agent performance analytics and coaching insights</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Cost analysis and efficiency metrics</span>
                </li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-teal-300 dark:hover:border-teal-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center mb-4">
                <HiOutlineDocumentText className="text-teal-600 dark:text-teal-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Supervisor Control Panel</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Override AI evaluations with human expertise</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Re-score calls for testing model improvements</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Batch processing management and priority queuing</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>Compliance reports and audit trail access</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-600 dark:text-teal-400 mt-1">•</span>
                  <span>API endpoint management and usage analytics</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Policy Management */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <FaFileAlt className="text-amber-600 dark:text-amber-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Policy Template & Criteria Management
            </h2>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
            <p className="text-gray-600 dark:text-gray-400 mb-6 text-lg leading-relaxed">
              Create and manage custom evaluation criteria tailored to your company's specific policies:
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-5 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/30">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-3">
                  <FaFileAlt className="text-amber-600 dark:text-amber-400 text-lg" />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Template Management</h3>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Create templates per company</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Template name, description, enabled/disabled toggle</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Archive/activate templates</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>View version history</span>
                  </li>
                </ul>
              </div>
              <div className="p-5 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/30">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-3">
                  <HiOutlineSparkles className="text-amber-600 dark:text-amber-400 text-lg" />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Evaluation Criteria</h3>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Category name (e.g., "Compliance", "Empathy", "Resolution")</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Weight (%) — must sum to 100</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Passing score (0-100)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Custom LLM evaluation prompt</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 dark:text-amber-400 mt-1">•</span>
                    <span>Edit/delete existing criteria</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Real-Time Notifications */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center">
              <FaBell className="text-pink-600 dark:text-pink-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Real-Time Notifications & Updates
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-pink-300 dark:hover:border-pink-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center mb-4">
                <HiOutlineSparkles className="text-pink-600 dark:text-pink-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">WebSocket Updates</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Supabase Realtime-powered instant status changes (queued → processing → completed).
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-pink-300 dark:hover:border-pink-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center mb-4">
                <FaEnvelope className="text-pink-600 dark:text-pink-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Email Notifications</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Email alerts when batch completes or fails.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-pink-300 dark:hover:border-pink-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center mb-4">
                <FaMobileAlt className="text-pink-600 dark:text-pink-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">In-App Notifications</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Toast notifications for errors, completions, and important updates.
              </p>
            </div>
          </div>
        </section>

        {/* Security & Privacy */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <FaLock className="text-red-600 dark:text-red-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Security & Privacy
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                <FaShieldVirus className="text-red-600 dark:text-red-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Row Level Security</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Users only access their company's data. Complete data isolation enforced at the database level.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                <FaKey className="text-red-600 dark:text-red-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Authentication</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                JWT-based authentication via Supabase Auth with secure token management.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                <FaLock className="text-red-600 dark:text-red-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Encryption</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                All data encrypted in transit (HTTPS) and at rest. Signed URLs for temporary secure file access.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                <FaHistory className="text-red-600 dark:text-red-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-lg">Audit Trail</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Complete logging of all uploads, evaluations, and policy changes with user and timestamp tracking.
              </p>
            </div>
          </div>
        </section>

        {/* Performance & Scalability */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <FaTachometerAlt className="text-emerald-600 dark:text-emerald-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Performance & Scalability
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
                <FaTachometerAlt className="text-emerald-600 dark:text-emerald-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">High Performance</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Process 100 recordings in parallel</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Total batch processing time {'<'}10 minutes for 100 files</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Dashboard load time {'<'}2 seconds</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Real-time notifications {'<'}500ms latency</span>
                </li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
                <FaServer className="text-emerald-600 dark:text-emerald-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Enterprise Scalability</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Auto-scale Edge Functions based on queue depth</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Support 1000+ concurrent users</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>Handle files up to 2GB</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 dark:text-emerald-400 mt-1">•</span>
                  <span>99.5% uptime with automatic retry on API failures</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Enterprise Technical Stack */}
        <section>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-900/30 flex items-center justify-center">
              <FaServer className="text-slate-600 dark:text-slate-400 text-2xl" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Enterprise Technical Stack
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-900/30 flex items-center justify-center mb-4">
                <FaDatabase className="text-slate-600 dark:text-slate-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Backend & Data</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>PostgreSQL with SQLAlchemy ORM</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>FastAPI with async processing</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Alembic database migrations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Redis for session & caching</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Comprehensive audit trails</span>
                </li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-900/30 flex items-center justify-center mb-4">
                <FaReact className="text-slate-600 dark:text-slate-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Frontend & Analytics</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>React 18 + TypeScript</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Supervisor dashboard with analytics</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Real-time batch processing monitoring</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Advanced filtering and search</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>API integration and management</span>
                </li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-200 shadow-sm hover:shadow-md">
              <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-900/30 flex items-center justify-center mb-4">
                <FaBrain className="text-slate-600 dark:text-slate-400 text-lg" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">AI & ML Pipeline</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Deepgram Nova-2 ASR</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Gemini 1.5 Flash/Pro hybrid</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>WhisperX forced alignment</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>8-class emotion classifier</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-600 dark:text-slate-400 mt-1">•</span>
                  <span>Continuous learning & fine-tuning</span>
                </li>
              </ul>
            </div>
          </div>
        </section>
      </div>
      </div>
    </div>
  )
}

