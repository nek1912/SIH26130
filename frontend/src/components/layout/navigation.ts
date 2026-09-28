export interface NavLink {
  to: string
  label: string
}

// Single source of truth for primary navigation. Consumed by both the
// desktop Sidebar and the MobileNav drawer so route/RBAC visibility is
// defined in exactly one place.
export const applicantLinks: NavLink[] = [
  { to: '/projects', label: 'Projects' },
]

export const staffLinks: NavLink[] = [
  { to: '/queue', label: 'Application Queue' },
]
