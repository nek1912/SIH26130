import { type SelectHTMLAttributes, forwardRef } from 'react'

// Compact native select used by the analysis/rehearsal/handoff panels. Keeps
// the panels' established compact treatment; the taller h-10 form style used
// by filter bars stays where it is. No custom dropdown behavior.
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className = '', children, ...props }, ref) => (
    <select ref={ref} className={`rounded-md border px-2 py-1 text-sm ${className}`} {...props}>
      {children}
    </select>
  ),
)
Select.displayName = 'Select'
