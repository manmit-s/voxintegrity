import React from 'react'
import { Link } from 'react-router-dom'

const screens = {
  capture: { file: 'capture.html', label: 'CAPTURE' },
  telemetry: { file: 'telemetry.html', label: 'TELEMETRY' },
  summary: { file: 'summary.html', label: 'SUMMARY' },
}

export default function StitchScreen({ screen }) {
  const current = screens[screen] || screens.capture

  return <div className="stitch-host">
    <iframe title={`Vaani Kavach ${current.label.toLowerCase()} screen`} src={`/stitch/${current.file}`} />
    <nav className="stitch-switcher" aria-label="Stitch screens">
      {Object.entries(screens).map(([key, item]) => <Link className={key === screen ? 'active' : ''} key={key} to={key === 'capture' ? '/verify' : `/${key}`}>{item.label}</Link>)}
    </nav>
  </div>
}