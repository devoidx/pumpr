import './Privacy.css'

const LAST_UPDATED = '17 April 2026'

export default function Privacy() {
  return (
    <div className="privacy-page">
      <div className="privacy-inner">
        <h1 className="privacy-title">Privacy Policy</h1>
        <p className="privacy-updated">Last updated: {LAST_UPDATED}</p>

        <div className="privacy-section">
          <h2>Overview</h2>
          <p>
            Pumpr is a free, open-source UK fuel price and EV charging finder.
            We take your privacy seriously. This policy explains what data we
            collect, how we use it, and your rights.
          </p>
          <p>
            The short version: we collect almost nothing. Your location is used
            only in your browser to find nearby stations and is never sent to
            our servers or stored anywhere.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Data we collect</h2>

          <h3>Location data</h3>
          <p>
            If you choose to share your location, it is used only within your
            browser to calculate distances to nearby fuel stations and EV
            chargers. Your coordinates are sent to our API solely to retrieve
            nearby results and are not logged, stored, or shared with any
            third party.
          </p>
          <p>
            You can also search by postcode instead of sharing your location.
            Postcodes are looked up via the publicly available postcodes.io
            service and are not stored by us.
          </p>

          <h3>Local storage</h3>
          <p>
            We store your last searched location, selected fuel type, and
            search radius in your browser's local storage so the app remembers
            your preferences between visits. This data never leaves your device.
            You can clear it at any time by clearing your browser's site data.
          </p>

          <h3>Server logs</h3>
          <p>
            Our servers may retain standard web server access logs (IP address,
            timestamp, endpoint requested) for up to 7 days for security and
            debugging purposes. These are not shared with third parties and are
            deleted automatically.
          </p>

          <h3>What we do not collect</h3>
          <ul>
            <li>We do not require you to create an account</li>
            <li>We do not use cookies for tracking or advertising</li>
            <li>We do not use third-party analytics (no Google Analytics, etc.)</li>
            <li>We do not sell or share your data with advertisers</li>
            <li>We do not track you across websites or apps</li>
          </ul>
        </div>

        <div className="privacy-section">
          <h2>Third-party data sources</h2>
          <p>
            Pumpr displays data from the following third-party sources. When
            you use Pumpr, your browser may make requests to these services:
          </p>
          <ul>
            <li>
              <strong>GOV.UK Fuel Finder</strong> — fuel price data is fetched
              by our servers on your behalf. We do not send your location to
              GOV.UK.
            </li>
            <li>
              <strong>Open Charge Map</strong> — EV charger data is fetched by
              our servers. Your approximate location (bounding box) may be sent
              to Open Charge Map to retrieve nearby chargers.
            </li>
            <li>
              <strong>postcodes.io</strong> — if you use postcode search, your
              postcode is sent to postcodes.io to retrieve coordinates. See
              their privacy policy at postcodes.io.
            </li>
            <li>
              <strong>CartoDB/CARTO</strong> — map tiles are loaded from
              CARTO's tile servers. Your IP address may be visible to CARTO
              when loading map tiles.
            </li>
            <li>
              <strong>Google Fonts</strong> — fonts are loaded from Google's
              servers. Your IP address may be visible to Google.
            </li>
          </ul>
        </div>

        <div className="privacy-section">
          <h2>Children's privacy</h2>
          <p>
            Pumpr is not directed at children under 13. We do not knowingly
            collect personal information from children.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Changes to this policy</h2>
          <p>
            We may update this privacy policy from time to time. Changes will
            be reflected on this page with an updated date. Continued use of
            Pumpr after changes constitutes acceptance of the updated policy.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Contact</h2>
          <p>
            If you have any questions about this privacy policy or how we
            handle your data, please contact us at:
          </p>
          <a href="mailto:hello@pumpr.app" className="privacy-contact">
            hello@pumpr.app
          </a>
        </div>

      </div>
    </div>
  )
}
