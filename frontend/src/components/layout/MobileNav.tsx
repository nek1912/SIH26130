import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { applicantLinks, staffLinks } from './navigation'

// Mobile navigation drawer. Reuses the Sidebar link data so route/RBAC
// visibility stays defined in exactly one place. Rendered only below lg;
// the desktop Sidebar is unchanged.
export function MobileNav() {
  const { role } = useAuth()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const links = role === 'APPLICANT' ? applicantLinks : staffLinks

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open ])

  const close = () => setOpen(false)

  return (
    <div className="lg:hidden">
      <button
        type="button"
        aria-label="Open navigation"
        aria-expanded={open}
        onClick={() => setOpen(true)}
        className="inline-flex h-10 w-10 items-center justify-center rounded-md hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>
      {open && (
        <div className="fixed inset-0 z-50">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={close}
            className="absolute inset-0 cursor-default bg-foreground/40"
          />
          <nav
            aria-label="Primary"
            className="absolute left-0 top-0 flex h-full w-60 flex-col border-r border-sidebar-border bg-sidebar"
          >
            <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
              <span className="text-sm font-semibold text-sidebar-foreground">GAIA</span>
              <button
                type="button"
                aria-label="Close navigation"
                onClick={close}
                className="inline-flex h-10 w-10 items-center justify-center rounded-md hover:bg-sidebar-foreground/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
            <div className="flex-1 space-y-1 p-2">
              {links.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={close}
                  className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    location.pathname.startsWith(link.to)
                      ? 'bg-sidebar-foreground/10 text-sidebar-foreground'
                      : 'text-sidebar-foreground/70 hover:bg-sidebar-foreground/5 hover:text-sidebar-foreground'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </div>
      )}
    </div>
  )
}
