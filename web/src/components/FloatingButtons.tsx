import { useState, useEffect } from 'react'
import { FaArrowUp, FaHeadset } from 'react-icons/fa'
import { SupportChat } from './SupportChat'

export function FloatingButtons() {
  const [isVisible, setIsVisible] = useState(false)
  const [isChatOpen, setIsChatOpen] = useState(false)

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > 300) {
        setIsVisible(true)
      } else {
        setIsVisible(false)
      }
    }

    window.addEventListener('scroll', toggleVisibility)
    return () => window.removeEventListener('scroll', toggleVisibility)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
        {/* Back to Top Button - Now on top */}
        {isVisible && (
          <button
            onClick={scrollToTop}
            className="flex items-center justify-center w-14 h-14 bg-gray-700 dark:bg-gray-800 text-white rounded-full shadow-lg hover:bg-gray-800 dark:hover:bg-gray-700 hover:shadow-xl transition-all duration-200 hover:scale-110"
            aria-label="Back to top"
            title="Back to top"
          >
            <FaArrowUp className="w-6 h-6" />
          </button>
        )}

        {/* Support Button - Now on bottom */}
        <button
          onClick={() => setIsChatOpen(!isChatOpen)}
          className={`group flex items-center justify-center w-14 h-14 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-110 ${
            isChatOpen
              ? 'bg-gray-700 dark:bg-gray-600 text-white'
              : 'bg-brand-500 text-white hover:bg-brand-600'
          }`}
          aria-label="Contact Support"
          title={isChatOpen ? 'Close Support Chat' : 'Contact Support'}
        >
          <FaHeadset className="w-6 h-6 group-hover:scale-110 transition-transform" />
        </button>
      </div>

      {/* Support Chat Widget */}
      {isChatOpen && <SupportChat onClose={() => setIsChatOpen(false)} />}
    </>
  )
}

