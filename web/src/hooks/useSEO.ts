import { useEffect } from 'react'

interface SEOProps {
  title?: string
  description?: string
  keywords?: string
  image?: string
  url?: string
  type?: 'website' | 'article'
  noindex?: boolean
}

export const useSEO = ({
  title,
  description,
  keywords,
  image = '/og-image.jpg',
  url,
  type = 'website',
  noindex = false
}: SEOProps) => {
  useEffect(() => {
    // Update document title
    if (title) {
      document.title = title
    }

    // Update meta tags
    const updateMetaTag = (name: string, content: string, property = false) => {
      const attribute = property ? 'property' : 'name'
      let element = document.querySelector(`meta[${attribute}="${name}"]`) as HTMLMetaElement

      if (element) {
        element.content = content
      } else {
        element = document.createElement('meta')
        element.setAttribute(attribute, name)
        element.content = content
        document.head.appendChild(element)
      }
    }

    // Update description
    if (description) {
      updateMetaTag('description', description)
      updateMetaTag('og:description', description, true)
      updateMetaTag('twitter:description', description, true)
    }

    // Update keywords
    if (keywords) {
      updateMetaTag('keywords', keywords)
    }

    // Update Open Graph tags
    if (title) {
      updateMetaTag('og:title', title, true)
      updateMetaTag('twitter:title', title, true)
    }

    if (image) {
      updateMetaTag('og:image', image, true)
      updateMetaTag('twitter:image', image, true)
    }

    if (url) {
      updateMetaTag('og:url', url, true)
      updateMetaTag('twitter:url', url, true)
    }

    if (type) {
      updateMetaTag('og:type', type, true)
    }

    // Update robots meta tag
    if (noindex) {
      updateMetaTag('robots', 'noindex, nofollow')
    } else {
      updateMetaTag('robots', 'index, follow')
    }

    // Update canonical URL
    let canonicalLink = document.querySelector('link[rel="canonical"]') as HTMLLinkElement
    if (url) {
      if (canonicalLink) {
        canonicalLink.href = url
      } else {
        canonicalLink = document.createElement('link')
        canonicalLink.rel = 'canonical'
        canonicalLink.href = url
        document.head.appendChild(canonicalLink)
      }
    }

    // Update JSON-LD structured data for breadcrumbs
    const updateBreadcrumbSchema = (path: string) => {
      const pathSegments = path.split('/').filter(Boolean)
      const breadcrumbs = [
        { position: 1, name: 'Home', item: '/' }
      ]

      let currentPath = ''
      pathSegments.forEach((segment, index) => {
        currentPath += `/${segment}`
        const name = segment.charAt(0).toUpperCase() + segment.slice(1).replace('-', ' ')
        breadcrumbs.push({
          position: index + 2,
          name,
          item: currentPath
        })
      })

      let breadcrumbScript = document.querySelector('script[data-breadcrumb]') as HTMLScriptElement
      if (breadcrumbScript) {
        breadcrumbScript.remove()
      }

      breadcrumbScript = document.createElement('script')
      breadcrumbScript.type = 'application/ld+json'
      breadcrumbScript.setAttribute('data-breadcrumb', 'true')
      breadcrumbScript.textContent = JSON.stringify({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs.map(crumb => ({
          "@type": "ListItem",
          "position": crumb.position,
          "name": crumb.name,
          "item": crumb.item
        }))
      })
      document.head.appendChild(breadcrumbScript)
    }

    if (url) {
      updateBreadcrumbSchema(url)
    }

  }, [title, description, keywords, image, url, type, noindex])
}

// Predefined SEO configurations for different pages
export const pageSEO = {
  home: {
    title: 'Qualitidex | Intelligent Call Center Quality Assurance',
    description: 'Transform your call center operations with AI-powered quality assurance. Upload recordings, get instant evaluations using custom policies. 90-97% cost reduction vs manual QA.',
    keywords: 'AI QA system, call center quality assurance, speech-to-text evaluation, automated QA, customer service evaluation, policy compliance, call center analytics',
    url: '/'
  },
  features: {
    title: 'Features | Qualitidex for Call Centers',
    description: 'Discover powerful features including custom policy templates, real-time transcription, advanced analytics, and enterprise-grade security for comprehensive QA evaluation.',
    keywords: 'QA features, call center automation, policy templates, real-time analytics, enterprise security, batch processing',
    url: '/features'
  },
  pricing: {
    title: 'Pricing | Qualitidex - Affordable Call Center Quality Assurance',
    description: 'Choose the perfect plan for your call center. Free trial available. Transparent pricing with no hidden fees. Scale from startup to enterprise.',
    keywords: 'QA pricing, call center pricing, AI evaluation pricing, subscription plans, free trial',
    url: '/pricing'
  },
  faq: {
    title: 'FAQ | Qualitidex - Frequently Asked Questions',
    description: 'Get answers to common questions about AI-powered quality assurance, implementation, security, pricing, and technical specifications.',
    keywords: 'QA FAQ, call center questions, AI evaluation help, implementation guide, security questions',
    url: '/faq'
  },
  signIn: {
    title: 'Sign In | Qualitidex',
    description: 'Access your AI-powered quality assurance dashboard. Secure login for call center quality management.',
    keywords: 'sign in, login, QA dashboard, secure access',
    url: '/sign-in',
    noindex: true
  },
  dashboard: {
    title: 'Dashboard | Qualitidex',
    description: 'Monitor your call center quality assurance metrics, view evaluations, and manage policies from your personalized dashboard.',
    keywords: 'QA dashboard, evaluation results, quality metrics, policy management',
    url: '/dashboard',
    noindex: true
  },
  test: {
    title: 'Test Qualitidex | Upload Call Recordings for AI Evaluation',
    description: 'Upload call recordings and test our AI-powered quality assurance system. Get instant evaluations using advanced speech-to-text and LLM analysis.',
    keywords: 'test QA, upload recordings, AI evaluation demo, call analysis',
    url: '/test',
    noindex: true
  }
}
