/**
 * Simple SEO hook — sets document title, meta description, canonical URL, and robots meta.
 * Call at the top of any page component.
 */
import { useEffect } from 'react'

const BASE_URL = 'https://pumpr.co.uk'
const DEFAULT_DESC = 'Find the cheapest petrol and diesel near you. Live UK fuel prices updated every 30 minutes from 8,000+ stations.'

export function useSEO({ title, description, path, noindex = false }) {
  useEffect(() => {
    // Title
    document.title = title ? `${title} | Pumpr` : 'Pumpr — UK Fuel Price Tracker'

    // Meta description
    let descTag = document.querySelector('meta[name="description"]')
    if (!descTag) {
      descTag = document.createElement('meta')
      descTag.setAttribute('name', 'description')
      document.head.appendChild(descTag)
    }
    descTag.setAttribute('content', description || DEFAULT_DESC)

    // Canonical
    let canonical = document.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.setAttribute('rel', 'canonical')
      document.head.appendChild(canonical)
    }
    canonical.setAttribute('href', path ? `${BASE_URL}${path}` : BASE_URL)

    // Robots
    let robotsTag = document.querySelector('meta[name="robots"]')
    if (!robotsTag) {
      robotsTag = document.createElement('meta')
      robotsTag.setAttribute('name', 'robots')
      document.head.appendChild(robotsTag)
    }
    robotsTag.setAttribute('content', noindex ? 'noindex, nofollow' : 'index, follow')

    return () => {
      document.title = 'Pumpr — UK Fuel Price Tracker'
    }
  }, [title, description, path, noindex])
}
