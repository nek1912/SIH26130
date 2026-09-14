import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

const applicantLinks = [
  { to: '/projects', label: 'Projects' },
]

const staffLinks = [
  { to: '/queue', label: 'Application Queue' },
]

export function Sidebar() {
  const { role } = useAuth()
  const location = useLocation()
  const links = role === 'APPLICANT' ? applicantLinks : staffLinks

  return (
    <aside className="hidden w-60 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
      <div className="flex h-14 items-center border-b border-sidebar-border px-4">
        <Link to="/" className="text-sm font-semibold text-sidebar-foreground">
          GAIA
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              location.pathname.startsWith(link.to)
                ? 'bg-sidebar-foreground/10 text-sidebar-foreground'
                : 'text-sidebar-foreground/70 hover:bg-sidebar-foreground/5 hover:text-sidebar-foreground'
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
