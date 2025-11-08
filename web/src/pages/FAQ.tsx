import { 
  FaQuestionCircle,
  FaChevronDown,
  FaChevronUp
} from 'react-icons/fa'
import { useState } from 'react'

interface FAQItem {
  question: string
  answer: string
  category: 'pricing' | 'product' | 'technical' | 'support'
}

const faqData: FAQItem[] = [
  {
    category: 'pricing',
    question: 'How is pricing calculated?',
    answer: 'Pricing is based on the total hours of audio processed each month. Each plan includes a set number of hours, with additional hours charged at the overage rate. Unused hours do not roll over to the next month.'
  },
  {
    category: 'pricing',
    question: 'What counts as "processing"?',
    answer: 'Processing includes transcription, speaker diarization, LLM evaluation, scoring, and analytics generation. The time is calculated based on the actual duration of your audio files.'
  },
  {
    category: 'pricing',
    question: 'Can I change plans later?',
    answer: 'Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we\'ll prorate any charges or credits.'
  },
  {
    category: 'pricing',
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards, ACH transfers, and can arrange invoicing for Enterprise customers. All plans are billed monthly.'
  },
  {
    category: 'pricing',
    question: 'Is there a free trial?',
    answer: 'Yes! All new accounts get a 14-day free trial with 2 hours of audio processing included. No credit card required.'
  },
  {
    category: 'product',
    question: 'What audio formats are supported?',
    answer: 'We support MP3, WAV, M4A, MP4, MOV, and AVI formats. Files up to 2GB in size can be uploaded and processed.'
  },
  {
    category: 'product',
    question: 'How accurate is the AI evaluation?',
    answer: 'Our system achieves 85-92% accuracy on problem resolution detection. The LLM-powered evaluation uses your company-specific criteria to provide contextually relevant assessments, making it 2X better than keyword-based systems.'
  },
  {
    category: 'product',
    question: 'Can I customize the evaluation criteria?',
    answer: 'Absolutely! You can create unlimited custom policy templates with your own evaluation criteria, weights, passing scores, and LLM prompts. This ensures evaluations match your company\'s specific requirements.'
  },
  {
    category: 'product',
    question: 'How long does processing take?',
    answer: 'Processing time varies based on file length, but we can process 100 recordings in parallel with total batch processing time under 10 minutes for 100 files. Individual files typically process in 1-3 minutes.'
  },
  {
    category: 'product',
    question: 'Can I export the results?',
    answer: 'Yes! You can export transcripts as PDF and evaluation results as CSV. Professional and Enterprise plans include advanced export options with custom formatting.'
  },
  {
    category: 'technical',
    question: 'How secure is my data?',
    answer: 'We use enterprise-grade security including end-to-end encryption, Row Level Security (RLS) for data isolation, JWT-based authentication, and signed URLs for file access. All data is encrypted in transit (HTTPS) and at rest.'
  },
  {
    category: 'technical',
    question: 'Is my data isolated from other companies?',
    answer: 'Yes. We use multi-tenant architecture with Row Level Security (RLS) that ensures complete data isolation. Each company can only access their own data, evaluations, and recordings.'
  },
  {
    category: 'technical',
    question: 'Do you offer API access?',
    answer: 'Yes! Professional and Enterprise plans include API access for programmatic integration with your existing systems. We provide comprehensive API documentation and support.'
  },
  {
    category: 'technical',
    question: 'Can I deploy on-premise?',
    answer: 'On-premise deployment is available for Enterprise customers. Contact our sales team to discuss your requirements and deployment options.'
  },
  {
    category: 'technical',
    question: 'What AI models do you use?',
    answer: 'We use Deepgram Nova-3 for transcription, AssemblyAI for speaker diarization, and Google Gemini 2.0 Flash or Anthropic Claude 3.5 Sonnet for LLM evaluation. We continuously evaluate and upgrade to the best available models.'
  },
  {
    category: 'support',
    question: 'What kind of support do you provide?',
    answer: 'Starter plans include email support. Professional plans include priority support with faster response times. Enterprise plans include 24/7 priority support with a dedicated account manager.'
  },
  {
    category: 'support',
    question: 'Do you provide training?',
    answer: 'Yes! Enterprise customers receive comprehensive training and onboarding. We also provide documentation, video tutorials, and webinars for all customers.'
  },
  {
    category: 'support',
    question: 'What is your uptime SLA?',
    answer: 'Professional plans include a 99.5% uptime SLA. Enterprise plans include a 99.9% uptime SLA with guaranteed response times for issues.'
  },
  {
    category: 'support',
    question: 'Can I integrate with my existing systems?',
    answer: 'Yes! We offer API access and can work with Enterprise customers to build custom integrations with your CRM, ticketing systems, or other business tools.'
  }
]

const categories = [
  { id: 'all', label: 'All Questions' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'product', label: 'Product' },
  { id: 'technical', label: 'Technical' },
  { id: 'support', label: 'Support' }
]

export function FAQ() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [openItems, setOpenItems] = useState<Set<number>>(new Set())

  const toggleItem = (index: number) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        newSet.delete(index)
      } else {
        newSet.add(index)
      }
      return newSet
    })
  }

  const filteredFAQs = selectedCategory === 'all' 
    ? faqData 
    : faqData.filter(faq => faq.category === selectedCategory)

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Enhanced background lighting effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Large ambient lights */}
        <div className="absolute top-0 left-1/4 w-[700px] h-[700px] bg-brand-400/9 dark:bg-brand-500/4 rounded-full blur-[100px]"></div>
        <div className="absolute top-1/2 -right-40 w-[600px] h-[600px] bg-purple-400/8 dark:bg-purple-500/4 rounded-full blur-[90px]"></div>
        <div className="absolute bottom-0 -left-40 w-[650px] h-[650px] bg-blue-400/7 dark:bg-blue-500/3 rounded-full blur-[95px]"></div>
        
        {/* Medium accent lights */}
        <div className="absolute top-1/3 right-1/3 w-[450px] h-[450px] bg-emerald-400/5 dark:bg-emerald-500/2.5 rounded-full blur-[75px]"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-cyan-400/4 dark:bg-cyan-500/2 rounded-full blur-3xl"></div>
        
        {/* Gradient overlays for depth */}
        <div className="absolute inset-0 bg-gradient-to-t from-white/8 via-transparent to-transparent dark:from-transparent dark:via-transparent dark:to-brand-900/6"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.06),transparent_70%)] dark:bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.03),transparent_70%)]"></div>
      </div>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 relative">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-brand-100 dark:bg-brand-900/30 rounded-full mb-3">
          <FaQuestionCircle className="text-brand-600 dark:text-brand-400 text-2xl" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-3">
          Frequently Asked Questions
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Find answers to common questions about our AI-powered QA platform
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap justify-center gap-3 mb-12">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedCategory === category.id
                ? 'bg-brand-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {category.label}
          </button>
        ))}
      </div>

      {/* FAQ Items */}
      <div className="space-y-4">
        {filteredFAQs.map((faq, index) => {
          const originalIndex = faqData.indexOf(faq)
          const isOpen = openItems.has(originalIndex)
          
          return (
            <div
              key={originalIndex}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
            >
              <button
                onClick={() => toggleItem(originalIndex)}
                className="w-full px-6 py-5 text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
              >
                <span className="font-semibold text-gray-900 dark:text-white pr-8 flex-1">
                  {faq.question}
                </span>
                <div className="flex-shrink-0 transition-transform duration-200">
                  {isOpen ? (
                    <FaChevronUp className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  ) : (
                    <FaChevronDown className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  )}
                </div>
              </button>
              <div
                className={`overflow-hidden transition-all duration-300 ease-in-out ${
                  isOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
                }`}
              >
                <div className="px-6 py-5 border-t border-gray-100 dark:border-gray-700">
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed text-base">
                    {faq.answer}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Contact Section */}
      <div className="mt-16 bg-gradient-to-r from-brand-50 to-brand-100 dark:from-brand-900/20 dark:to-brand-800/20 rounded-xl p-8 border border-brand-200 dark:border-brand-800">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Still have questions?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Our support team is here to help you get the most out of our platform.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:support@qasystem.com?subject=FAQ Question"
              className="inline-flex items-center justify-center px-6 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors font-medium"
            >
              Contact Support
            </a>
            <a
              href="mailto:sales@qasystem.com?subject=Sales Inquiry"
              className="inline-flex items-center justify-center px-6 py-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium"
            >
              Talk to Sales
            </a>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}

