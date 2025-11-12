import { Link } from 'react-router-dom'
import { 
  FaLinkedin, 
  FaTwitter, 
  FaGithub, 
  FaEnvelope, 
  FaPhone, 
  FaMapMarkerAlt,
  FaArrowRight
} from 'react-icons/fa'

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 w-full">
      <div className="px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8 max-w-7xl mx-auto">
          {/* Company Info */}
          <div className="space-y-4">
            <Link to="/" className="flex items-center space-x-3">
              <img
                src="/Logo.svg"
                alt="Qualitidex"
                className="h-10 w-auto"
                loading="lazy"
                decoding="async"
              />
              <span className="font-bold text-gray-900 dark:text-white text-xl">
                Qualitidex
              </span>
            </Link>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              AI-powered quality assurance platform that transforms call center operations with intelligent evaluation and comprehensive analytics.
            </p>
            <div className="flex space-x-4">
              <a
                href="https://linkedin.com/company/your-company"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                aria-label="LinkedIn"
              >
                <FaLinkedin className="w-5 h-5" />
              </a>
              <a
                href="https://twitter.com/your-company"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                aria-label="Twitter"
              >
                <FaTwitter className="w-5 h-5" />
              </a>
              <a
                href="https://github.com/your-company"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                aria-label="GitHub"
              >
                <FaGithub className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Product
            </h3>
            <ul className="space-y-3">
              <li>
                <Link
                  to="/features"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Features
                </Link>
              </li>
              <li>
                <Link
                  to="/pricing"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Pricing
                </Link>
              </li>
              <li>
                <Link
                  to="/dashboard"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Dashboard
                </Link>
              </li>
              <li>
                <a
                  href="#integrations"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Integrations
                </a>
              </li>
              <li>
                <a
                  href="#api"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  API
                </a>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Company
            </h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="#about"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  About Us
                </a>
              </li>
              <li>
                <a
                  href="#blog"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Blog
                </a>
              </li>
              <li>
                <a
                  href="#careers"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Careers
                </a>
              </li>
              <li>
                <a
                  href="#contact"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Contact
                </a>
              </li>
              <li>
                <a
                  href="#partners"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Partners
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Resources
            </h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="#documentation"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="#support"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Support
                </a>
              </li>
              <li>
                <a
                  href="#community"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Community
                </a>
              </li>
              <li>
                <a
                  href="#status"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  System Status
                </a>
              </li>
              <li>
                <a
                  href="#changelog"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  Changelog
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Newsletter Section */}
        <div className="border-t border-gray-200 dark:border-gray-800 pt-8 mb-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Stay Updated
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Get the latest updates, product announcements, and tips delivered to your inbox.
              </p>
            </div>
            <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors font-medium flex items-center justify-center gap-2"
              >
                Subscribe
                <FaArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Contact Info */}
        <div className="border-t border-gray-200 dark:border-gray-800 pt-8 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm max-w-7xl mx-auto">
            <div className="flex items-start space-x-3">
              <FaEnvelope className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Email</p>
                <a
                  href="mailto:support@qualitidex.com"
                  className="text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  support@qualitidex.com
                </a>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <FaPhone className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Phone</p>
                <a
                  href="tel:+1-555-000-0000"
                  className="text-gray-600 dark:text-gray-400 hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                >
                  +1 (555) 000-0000
                </a>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <FaMapMarkerAlt className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Address</p>
                <p className="text-gray-600 dark:text-gray-400">
                  San Francisco, CA, USA
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-200 dark:border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 max-w-7xl mx-auto">
            <div className="flex flex-wrap justify-center md:justify-start gap-6 text-sm text-gray-600 dark:text-gray-400">
              <a
                href="#privacy"
                className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
              >
                Privacy Policy
              </a>
              <a
                href="#terms"
                className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
              >
                Terms of Service
              </a>
              <a
                href="#cookies"
                className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
              >
                Cookie Policy
              </a>
              <a
                href="#security"
                className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
              >
                Security
              </a>
              <a
                href="#compliance"
                className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
              >
                Compliance
              </a>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>
                &copy; {currentYear} Qualitidex. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

