import { Link } from 'react-router-dom'
import { 
  FaCloudUploadAlt, 
  FaBrain, 
  FaChartLine, 
  FaShieldAlt,
  FaClock,
  FaDollarSign,
  FaCheckCircle,
  FaRocket,
  FaFileAudio,
  FaCog,
  FaChartBar,
  FaBell
} from 'react-icons/fa'

export function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-[#0A0F1A] relative overflow-hidden">
      {/* Enhanced background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Large ambient lights */}
        <div className="absolute top-0 -left-40 w-[800px] h-[800px] bg-brand-400/15 dark:bg-brand-500/8 rounded-full blur-[120px]"></div>
        <div className="absolute top-1/4 -right-40 w-[700px] h-[700px] bg-blue-400/12 dark:bg-blue-500/6 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-purple-400/10 dark:bg-purple-500/5 rounded-full blur-[90px]"></div>
        
        {/* Medium accent lights */}
        <div className="absolute top-1/3 right-1/3 w-96 h-96 bg-emerald-400/8 dark:bg-emerald-500/4 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-0 w-[500px] h-[500px] bg-cyan-400/6 dark:bg-cyan-500/3 rounded-full blur-[80px]"></div>
        
        {/* Small highlight lights */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-brand-300/5 dark:bg-brand-400/3 rounded-full blur-2xl"></div>
        
        {/* Gradient overlay for depth */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white/5 dark:to-brand-900/10"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,transparent_0%,rgba(0,0,0,0.03)_100%)] dark:bg-[radial-gradient(circle_at_50%_50%,transparent_0%,rgba(0,0,0,0.1)_100%)]"></div>
      </div>
      
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-brand-50/50 via-white to-blue-50/30 dark:from-[#0A0F1A] dark:via-[#0A0F1A] dark:to-brand-900/30 overflow-hidden">
        {/* Additional hero section lighting */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-brand-100/20 to-transparent dark:via-brand-900/10"></div>
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-full h-full bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.1),transparent_70%)] dark:bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.05),transparent_70%)]"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Text Content */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-brand-500 to-brand-600 rounded-2xl mb-4 shadow-lg">
                <span className="text-white font-bold text-2xl">AI</span>
              </div>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4 tracking-tight">
                AI-Powered QA System
              </h1>
              <p className="text-base md:text-lg text-gray-600 dark:text-gray-400 mb-4 max-w-2xl lg:max-w-none mx-auto lg:mx-0 leading-relaxed">
                Transform your call center operations with intelligent quality assurance
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mb-8 max-w-xl lg:max-w-none mx-auto lg:mx-0">
                Upload call recordings → AI evaluates using custom company policies → Get comprehensive QA results in minutes
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link
                  to="/test"
                  className="inline-flex items-center justify-center px-8 py-4 bg-brand-500 text-white rounded-lg font-semibold hover:bg-brand-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200"
                >
                  Get Started
                  <FaRocket className="ml-2 w-5 h-5" />
                </Link>
                <Link
                  to="/features"
                  className="inline-flex items-center justify-center px-8 py-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg font-semibold border-2 border-gray-200 dark:border-gray-700 hover:border-brand-500 dark:hover:border-brand-500 transition-all duration-200"
                >
                  Learn More
                </Link>
              </div>
            </div>
            
            {/* Right Column - Hero Image */}
            <div className="relative lg:order-last">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl transform hover:scale-[1.02] transition-transform duration-300">
                {/* Image overlay for better text contrast */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent z-10"></div>
                <img 
                  src="https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
                  alt="Professional call center team working with AI-powered quality assurance system"
                  className="w-full h-[400px] md:h-[500px] lg:h-[600px] object-cover"
                  loading="eager"
                />
                {/* Decorative elements */}
                <div className="absolute top-4 right-4 w-20 h-20 bg-brand-500/20 backdrop-blur-sm rounded-lg border border-brand-400/30 z-20"></div>
                <div className="absolute bottom-4 left-4 w-16 h-16 bg-blue-500/20 backdrop-blur-sm rounded-lg border border-blue-400/30 z-20"></div>
              </div>
              {/* Floating badge */}
              <div className="absolute -bottom-6 -left-6 bg-white dark:bg-gray-800 rounded-xl p-4 shadow-xl border border-gray-200 dark:border-gray-700 hidden lg:block">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                    <FaCheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">100% Coverage</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Every call evaluated</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Value Proposition */}
      <div className="py-16 bg-white/80 dark:bg-[#0A0F1A]/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center p-6 rounded-xl bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border border-green-200 dark:border-green-800">
              <FaDollarSign className="w-10 h-10 text-green-600 dark:text-green-400 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">90-97%</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Cost Reduction</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">$0.50-2 vs $15-25 per call</p>
            </div>
            <div className="text-center p-6 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-800">
              <FaCheckCircle className="w-10 h-10 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">100%</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Call Coverage</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">vs 1-3% manual sampling</p>
            </div>
            <div className="text-center p-6 rounded-xl bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border border-purple-200 dark:border-purple-800">
              <FaBrain className="w-10 h-10 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">85-92%</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Accuracy</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Problem resolution detection</p>
            </div>
            <div className="text-center p-6 rounded-xl bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border border-orange-200 dark:border-orange-800">
              <FaChartLine className="w-10 h-10 text-orange-600 dark:text-orange-400 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">2X</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Better Results</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">vs keyword-based systems</p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              From upload to results in minutes with AI-powered evaluation
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-brand-100 dark:bg-brand-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FaCloudUploadAlt className="w-8 h-8 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-2xl font-bold text-brand-500 mb-2">1. Upload</div>
              <p className="text-gray-600 dark:text-gray-400">
                Drag and drop or browse to upload call recordings. Supports MP3, WAV, M4A, MP4 formats. Batch upload up to 100+ files.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FaFileAudio className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-blue-500 mb-2">2. Transcribe</div>
              <p className="text-gray-600 dark:text-gray-400">
                AI automatically transcribes audio using Deepgram Nova-3. Speaker diarization separates agent and customer speech.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FaBrain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-purple-500 mb-2">3. Evaluate</div>
              <p className="text-gray-600 dark:text-gray-400">
                LLM (Gemini/Claude) evaluates transcripts using your company-specific policies and evaluation criteria.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FaChartBar className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-2xl font-bold text-green-500 mb-2">4. Results</div>
              <p className="text-gray-600 dark:text-gray-400">
                Get comprehensive QA scores, policy violations, resolution detection, and coaching recommendations.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Features */}
      <div className="py-16 bg-white/80 dark:bg-[#0A0F1A]/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Key Features
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Everything you need for comprehensive quality assurance
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-brand-100 dark:bg-brand-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaCog className="w-6 h-6 text-brand-600 dark:text-brand-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Custom Policy Templates</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Create unlimited custom evaluation criteria tailored to your business. Define weights, passing scores, and LLM prompts.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaClock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Fast Processing</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Process 100+ recordings in parallel with total batch processing time under 10 minutes. Individual files process in 1-3 minutes.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaChartLine className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Advanced Analytics</h3>
              <p className="text-gray-600 dark:text-gray-400">
                View comprehensive QA scores, category breakdowns, policy violations, and resolution detection with confidence scores.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaBell className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Real-Time Notifications</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get instant WebSocket-powered updates on processing status. Email notifications when batches complete.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaShieldAlt className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Enterprise Security</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Row Level Security ensures data isolation. End-to-end encryption, JWT authentication, and signed URLs for file access.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-md hover:shadow-lg border border-gray-200 dark:border-gray-700 transition-shadow">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center mb-4">
                <FaChartBar className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Export & Reports</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Download transcripts as PDF and export evaluation results as CSV. Generate comprehensive reports for management.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Powered by Industry-Leading Technology
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Built on modern, scalable infrastructure
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Supabase</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Backend & Database</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Deepgram</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Speech-to-Text</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Gemini/Claude</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">LLM Evaluation</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">React</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Frontend Framework</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gradient-to-r from-brand-500 to-brand-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your QA Process?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Start your free trial today. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/test"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-brand-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors shadow-lg"
            >
              Start Free Trial
              <FaRocket className="ml-2 w-5 h-5" />
            </Link>
            <Link
              to="/pricing"
              className="inline-flex items-center justify-center px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition-colors"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
