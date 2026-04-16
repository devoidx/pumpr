import './ModeToggle.css'

export default function ModeToggle({ mode, onChange }) {
  return (
    <div className="mode-toggle">
      <button
        className={`mode-btn ${mode === 'fuel' ? 'active' : ''}`}
        onClick={() => onChange('fuel')}
      >
        ⛽ Fuel
      </button>
      <button
        className={`mode-btn ${mode === 'ev' ? 'active ev' : ''}`}
        onClick={() => onChange('ev')}
      >
        ⚡ EV
      </button>
    </div>
  )
}
