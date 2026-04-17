import './About.css'

const VERSION = '0.1.0'

export default function About() {
  return (
    <div className="about-page">
      <div className="about-inner">

        <div className="about-hero">
          <div className="about-logo">⛽</div>
          <h1 className="about-title">Pumpr</h1>
          <p className="about-tagline">Real-time UK fuel prices & EV charging</p>
          <span className="about-version">v{VERSION}</span>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">What is Pumpr?</h2>
          <p className="about-body">
            Pumpr helps UK drivers find the cheapest fuel and nearest EV charging points.
            Prices are updated every 30 minutes from the official GOV.UK Fuel Finder scheme,
            covering 7,600+ petrol stations across England, Scotland, Wales and Northern Ireland.
            EV charging data is powered by Open Charge Map.
          </p>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Data Sources</h2>
          <div className="about-sources">
            
              href="https://www.gov.uk/guidance/access-the-latest-fuel-prices-and-forecourt-data-via-api-or-email"
              target="_blank"
              rel="noopener noreferrer"
              className="about-source-card"
            >
              <div className="about-source-icon">🇬🇧</div>
              <div>
                <div className="about-source-name">GOV.UK Fuel Finder</div>
                <div className="about-source-desc">
                  Official UK government fuel price data under the Motor Fuel Price
                  (Open Data) Regulations 2025
                </div>
              </div>
            </a>
            
              href="https://openchargemap.org"
              target="_blank"
              rel="noopener noreferrer"
              className="about-source-card"
            >
              <div className="about-source-icon">⚡</div>
              <div>
                <div className="about-source-name">Open Charge Map</div>
                <div className="about-source-desc">
                  Community-maintained global registry of EV charging locations,
                  licensed under Creative Commons
                </div>
              </div>
            </a>
          </div>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Support Pumpr</h2>
          <p className="about-body">
            Pumpr is free to use and built by one developer in their spare time.
            If it saves you money at the pump, consider buying me a coffee!
          </p>
          
            href="https://ko-fi.com/pumprapp"
            target="_blank"
            rel="noopener noreferrer"
            className="about-kofi-btn"
          >
            ☕ Support on Ko-fi
          </a>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Follow</h2>
          <div className="about-social">
            
              href="https://x.com/pumprapp"
              target="_blank"
              rel="noopener noreferrer"
              className="about-social-link"
            >
              <span className="about-social-icon">𝕏</span>
              <span>@pumprapp</span>
            </a>
            
              href="https://bsky.app/profile/pumprapp.bsky.social"
              target="_blank"
              rel="noopener noreferrer"
              className="about-social-link"
            >
              <span className="about-social-icon">🦋</span>
              <span>pumprapp.bsky.social</span>
            </a>
            
              href="https://github.com/devoidx/pumpr"
              target="_blank"
              rel="noopener noreferrer"
              className="about-social-link"
            >
              <span className="about-social-icon">⌥</span>
              <span>devoidx/pumpr</span>
            </a>
          </div>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Contact</h2>
          <p className="about-body">
            Found incorrect data or have a suggestion?
          </p>
          <a href="mailto:hello@pumpr.app" className="about-contact-link">
            hello@pumpr.app
          </a>
        </div>

        <div className="about-section">
          <h2 className="about-section-title">Legal</h2>
          <p className="about-body about-legal">
            Fuel price data is provided as-is from the GOV.UK Fuel Finder scheme.
            Prices may be up to 30 minutes old. Always verify prices at the pump
            before filling up. Pumpr is not affiliated with or endorsed by the
            UK Government, VE3 Global Ltd, or Open Charge Map.
          </p>
          <div className="about-legal-links">
            <a href="/privacy" className="about-legal-link">Privacy Policy</a>
          </div>
        </div>

      </div>
    </div>
  )
}
