import { ApiError } from './api'

// Normalize caught API/JS errors to a display string. Mirrors the exact
// branching previously copy-pasted across handlers: ApiError and Error
// contribute their message, anything else falls back to the caller message.
export function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return fallback
}
