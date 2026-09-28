export function LoadingSpinner({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      {/* Static ring under reduced motion; surrounding loading text preserves meaning. */}
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-border border-t-primary motion-reduce:animate-none" />
    </div>
  )
}
