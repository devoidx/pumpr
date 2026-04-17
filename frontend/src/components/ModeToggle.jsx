import PumpIcon from './icons/PumpIcon'
import BoltIcon from './icons/BoltIcon'
import './ModeToggle.css'

export default function ModeToggle({ mode, onChange }) {
  return (
    <div className="mode-toggle">
      <button
        className={`mode-btn ${mode === 'fuel' ? 'active' : ''}`}
        onClick={() => onChange('fuel')}
        title="Fuel stations"
      >
        <PumpIcon size={14} color={mode === 'fuel' ? '#f5a623' : '#888'} />
        <span>Fuel</span>
      </button>
      <button
        className={`mode-btn ${mode === 'ev' ? 'active ev' : ''}`}
        onClick={() => onChange('ev')}
        title="EV charging"
      >
        <BoltIcon size={14} color={mode === 'ev' ? '#2ecc71' : '#888'} />
        <span>EV</span>
      </button>
    </div>
  )
}
