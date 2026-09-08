import React from 'react'

/**
 * Keep a rendering error visible during a demo instead of leaving the browser
 * with an unexplained blank page. The browser console still contains the full
 * error and a reload gives the operator a quick recovery path.
 */
export default class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <main style={{ minHeight: '100vh', padding: '2rem', background: '#0A0D12', color: '#e1e2ea', fontFamily: 'system-ui, sans-serif' }}>
        <h1 style={{ marginTop: 0 }}>Vaani Kavach could not render</h1>
        <p>The interface hit an unexpected error. Reload the page to start a fresh session.</p>
        <pre style={{ whiteSpace: 'pre-wrap', color: '#ffb4a6' }}>{this.state.error.message}</pre>
        <button type="button" onClick={() => window.location.reload()} style={{ padding: '.7rem 1rem', cursor: 'pointer' }}>Reload application</button>
      </main>
    )
  }
}
