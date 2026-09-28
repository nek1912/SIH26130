import { type InputHTMLAttributes, forwardRef } from 'react'

// Compact single-line text input used by the analysis/rehearsal/handoff
// panels. Mirrors the shared Select's compact treatment verbatim
// (`rounded-md border px-2 py-1 text-sm`); callers add their own width via
// className. The taller h-10 Input stays for full form bars and dialog-style
// fields. Checkbox, radio, and file inputs keep their distinct semantics and
// must NOT be converted to this.
export const TextInput = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className = '', ...props }, ref) => (
    <input ref={ref} className={`rounded-md border px-2 py-1 text-sm ${className}`} {...props} />
  ),
)
TextInput.displayName = 'TextInput'
