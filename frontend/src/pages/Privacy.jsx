import './Privacy.css'

const LAST_UPDATED = '28 May 2026'

export default function Privacy() {
  return (
    <div className="privacy-page">
      <div className="privacy-inner">
        <h1 className="privacy-title">Privacy Policy</h1>
        <p className="privacy-updated">Last updated: {LAST_UPDATED}</p>

        <div className="privacy-section">
          <h2>Overview</h2>
          <p>
            Pumpr is a UK fuel price tracker available on web and Android.
            This policy explains what data we collect, how we use it, and your rights.
          </p>
          <p>
            The short version: we collect only what is necessary to provide the service.
            Your location is used only to find nearby stations and is never stored.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Data we collect</h2>

          <h3>Location data</h3>
          <p>
            If you choose to share your location, it is used to retrieve nearby fuel stations.
            Your coordinates are sent to our API to return results and are not logged, stored,
            or shared with any third party.
          </p>

          <h3>Account data (Pro subscribers)</h3>
          <p>
            If you subscribe to Pumpr Pro, we collect your email address to create your account.
            You may optionally set a display name. We store your preferences (fuel type, economy units,
            driving distance mode) and any data you choose to add: saved places, vehicles, price alerts,
            and fuel fill-up logs.
          </p>
          <p>
            Account creation is handled via Stripe payment processing. We do not store payment card details —
            these are handled entirely by Stripe. See <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer">Stripe's privacy policy</a>.
          </p>

          <h3>Analytics</h3>
          <p>
            We use self-hosted Umami analytics to understand how people use Pumpr. Umami is privacy-focused
            and does not use cookies or track you across websites. It collects anonymised page views and events
            (such as which features are used). No personal data is shared with third parties through analytics.
          </p>

          <h3>Server logs</h3>
          <p>
            Our servers retain standard web server access logs (IP address, timestamp, endpoint requested)
            for up to 7 days for security and debugging. These are not shared with third parties.
          </p>

          <h3>Local storage</h3>
          <p>
            We store your last searched location, selected fuel type, and search radius in your browser's
            local storage so the app remembers your preferences. This data never leaves your device.
          </p>

          <h3>What we do not collect</h3>
          <ul>
            <li>We do not use cookies for tracking or advertising</li>
            <li>We do not use Google Analytics or other third-party tracking</li>
            <li>We do not sell or share your data with advertisers</li>
            <li>We do not track you across websites or apps</li>
          </ul>
        </div>

        <div className="privacy-section">
          <h2>Email communications</h2>
          <p>
            If you opt in, we may send you email newsletters when new fuel price insights are published,
            and a monthly fuel spending digest if you use the fuel tracker. You can unsubscribe at any time
            from your profile settings or via the unsubscribe link in any email.
          </p>
          <p>
            Transactional emails (account setup, password reset, price alerts) are sent as part of the service
            and cannot be opted out of while your account is active.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Third-party services</h2>
          <ul>
            <li><strong>GOV.UK Fuel Finder</strong> — fuel price data fetched by our servers. We do not send your location to GOV.UK.</li>
            <li><strong>Stripe</strong> — payment processing for Pro subscriptions. See <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer">Stripe's privacy policy</a>.</li>
            <li><strong>Resend</strong> — transactional email delivery.</li>
            <li><strong>postcodes.io</strong> — postcode to coordinate lookup for search.</li>
            <li><strong>MaxMind GeoLite2</strong> — IP-based country/city detection for analytics (self-hosted, no data sent to MaxMind).</li>
            <li><strong>DVLA VES API</strong> — vehicle lookup by registration plate for the My Vehicles feature.</li>
            <li><strong>OSRM / OpenStreetMap</strong> — driving distance calculations for Pro users.</li>
          </ul>
        </div>

        <div className="privacy-section">
          <h2>Data retention</h2>
          <p>
            Account data is retained while your account is active. If you cancel your subscription and your
            account is deleted, your personal data is removed within 30 days. Fuel fill-up logs, saved places,
            and vehicles are deleted immediately when you remove them or when your account is closed.
          </p>
          <p>
            Price history data is anonymised (not linked to any user) and retained for up to 90 days.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Your rights</h2>
          <p>
            Under UK GDPR you have the right to access, correct, or delete your personal data.
            To exercise these rights, contact us at <a href="mailto:hello@pumpr.co.uk">hello@pumpr.co.uk</a>.
            You can also manage most of your data directly from your profile settings.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Children's privacy</h2>
          <p>
            Pumpr is not directed at children under 13. We do not knowingly collect personal information from children.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Changes to this policy</h2>
          <p>
            We may update this privacy policy from time to time. Changes will be reflected on this page with an updated date.
          </p>
        </div>

        <div className="privacy-section">
          <h2>Contact</h2>
          <p>Questions about this policy? Contact us at:</p>
          <a href="mailto:hello@pumpr.co.uk" className="privacy-contact">hello@pumpr.co.uk</a>
        </div>

      </div>
    </div>
  )
}