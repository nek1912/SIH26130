// Presentation-level date formatting. Bodies intentionally mirror the exact
// expressions previously inlined at call sites (same input, same output);
// locale handling can be revisited in one place if requirements change.

/** Format an ISO date string as a short date (e.g. due dates, created dates). */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

/** Format an ISO date string with time (e.g. audit/check timestamps). */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString()
}
