import { useEffect } from 'react'
import './About.css'
import { useSEO } from '../hooks/useSEO'

const GOV_URL = 'https://www.gov.uk/guidance/access-the-latest-fuel-prices-and-forecourt-data-via-api-or-email'

export default function FuelFinder() {
  useSEO({
    title: 'UK Fuel Finder Scheme Explained, with Live Prices',
    description: 'What is the GOV.UK Fuel Finder scheme? How it works, what data it covers, and how Pumpr uses it to show live petrol and diesel prices at 8,000+ UK stations.',
    path: '/fuel-finder',
  })
  useEffect(() => { if (typeof umami !== 'undefined') umami.track('fuel-finder-viewed') }, [])
  return (
    <div className="about-page">
      <div className="about-inner">
        <div className="about-hero">
          <h1 className="about-title">UK Fuel Finder: what it is and how to use it</h1>
          <p className="about-tagline">Live petrol and diesel prices from the official GOV.UK scheme</p>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">What is the Fuel Finder scheme?</h2>
          <p className="about-body">
            Fuel Finder is the UK government's open data scheme for road fuel prices. Under the
            Motor Fuel Price (Open Data) Regulations 2025, fuel retailers report their pump prices
            to the government, which publishes them as open data. Developers and apps can then
            use that data to show drivers where fuel is cheapest. The official guidance is on{' '}
            <a href={GOV_URL} target="_blank" rel="noopener noreferrer">GOV.UK</a>.
          </p>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">How does Pumpr use Fuel Finder data?</h2>
          <p className="about-body">
            Pumpr is a free, independent app built on the Fuel Finder feed. It checks the feed every
            30 minutes and shows live petrol (E10, E5) and diesel prices for more than 8,000 stations
            across England, Scotland, Wales and Northern Ireland. You can search by postcode or
            location, sort by price or distance, and see price history and which day of the week is
            usually cheapest.
          </p>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Find cheap fuel near you</h2>
          <p className="about-body">
            Start on the <a href="/">Pumpr home page</a> to search your postcode, or jump straight to a city:{' '}
            <a href="/cheap-fuel/london">London</a>,{' '}
            <a href="/cheap-fuel/manchester">Manchester</a>,{' '}
            <a href="/cheap-fuel/birmingham">Birmingham</a>,{' '}
            <a href="/cheap-fuel/leeds">Leeds</a>,{' '}
            <a href="/cheap-fuel/glasgow">Glasgow</a>,{' '}
            <a href="/cheap-fuel/cardiff">Cardiff</a> and{' '}
            <a href="/cheap-fuel/belfast">Belfast</a>.
            Driving abroad? See <a href="/europe">fuel prices in France, Italy, Spain and Germany</a>.
          </p>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Good to know</h2>
          <p className="about-body">
            Prices come from what retailers report, so a price can occasionally lag what is on the
            forecourt sign. Some stations, such as Costco, need a membership to buy fuel; Pumpr marks
            these as members only. Read more <a href="/about">about Pumpr</a> and its data sources.
          </p>
        </div>
      </div>
    </div>
  )
}
