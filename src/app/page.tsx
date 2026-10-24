'use client'

import { useEffect } from 'react'

/**
 * Redirect root page to YFG Accounting Desk frontend.
 *
 * The YFG app is a complete FastAPI + static frontend served from /static/.
 * Next.js just acts as a proxy for /api/* requests to the FastAPI backend at port 8000.
 *
 * Visiting / will automatically redirect to /static/index.html where the actual
 * login page and YFG UI live.
 */
export default function Home() {
  useEffect(() => {
    // Use window.location for hard redirect (so browser loads /static/index.html fresh)
    if (typeof window !== 'undefined') {
      window.location.replace('/static/index.html')
    }
  }, [])

  return (
    <div
      dir="rtl"
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Tahoma, "Segoe UI", sans-serif',
        background: 'linear-gradient(135deg, #0b8f89 0%, #123d4a 100%)',
        color: 'white',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'linear-gradient(145deg, #38c7b8, #06918c)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '32px',
            fontWeight: 800,
            marginBottom: '24px',
            boxShadow: '0 12px 32px rgba(0,0,0,0.3)',
          }}
        >
          Y
        </div>
        <h1 style={{ fontSize: '24px', marginBottom: '8px', margin: 0 }}>YFG Accounting Desk</h1>
        <p style={{ opacity: 0.85, fontSize: '14px', marginTop: '8px' }}>
          در حال انتقال به میزکار حسابداری...
        </p>
        <a
          href="/static/index.html"
          style={{
            display: 'inline-block',
            marginTop: '24px',
            padding: '12px 32px',
            background: 'white',
            color: '#0b8f89',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 600,
            boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
          }}
        >
          اگر انتقال نشد، اینجا کلیک کنید
        </a>
      </div>
    </div>
  )
}
