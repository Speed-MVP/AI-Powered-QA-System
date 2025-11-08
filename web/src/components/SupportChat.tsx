import { useState, useEffect, useRef } from 'react'
import { FaTimes, FaPaperPlane, FaHeadset } from 'react-icons/fa'

interface Message {
  id: string
  text: string
  sender: 'user' | 'support'
  timestamp: Date
}

interface SupportChatProps {
  onClose: () => void
}

export function SupportChat({ onClose }: SupportChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! How can we help you today?',
      sender: 'support',
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, newMessage])
    setInputMessage('')

    // Simulate support response
    setTimeout(() => {
      const supportResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Thank you for your message! Our support team will get back to you shortly. You can also email us at support@qasystem.com for immediate assistance.',
        sender: 'support',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, supportResponse])
    }, 1000)
  }

  return (
    <div className="fixed bottom-6 right-24 w-80 h-[500px] bg-white dark:bg-gray-800 rounded-lg shadow-2xl z-50 flex flex-col border border-gray-200 dark:border-gray-700 transform transition-all duration-200 ease-out">
        {/* Header */}
        <div className="bg-brand-500 text-white px-4 py-3 rounded-t-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FaHeadset className="w-5 h-5" />
            <div>
              <h3 className="font-semibold text-sm">Support Chat</h3>
              <p className="text-xs text-brand-100">We typically reply in a few minutes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 transition-colors p-1"
            aria-label="Close chat"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[75%] rounded-lg px-3 py-2 ${
                  message.sender === 'user'
                    ? 'bg-brand-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                <p className="text-xs mt-1 opacity-70">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="border-t border-gray-200 dark:border-gray-700 p-3">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              autoFocus
            />
            <button
              type="submit"
              className="p-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
              aria-label="Send message"
            >
              <FaPaperPlane className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Or email us at{' '}
            <a
              href="mailto:support@qasystem.com"
              className="text-brand-500 hover:text-brand-600"
            >
              support@qasystem.com
            </a>
          </p>
        </form>
    </div>
  )
}

