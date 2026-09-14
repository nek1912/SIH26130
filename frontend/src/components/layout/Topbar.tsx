import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

export function Topbar() {
  const { session, role, signOut } = useAuth()
  const email = session?.user?.email ?? ''

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-4 lg:px-6">
      <div className="lg:hidden">
        <span className="text-sm font-semibold">GAIA</span>
      </div>
      <div className="flex flex-1 items-center justify-end gap-4">
        <span className="text-xs text-muted-foreground">
          {email} <span className="ml-1 rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase">{role}</span>
        </span>
        <Button variant="ghost" size="sm" onClick={signOut}>
          Sign out
        </Button>
      </div>
    </header>
  )
}
