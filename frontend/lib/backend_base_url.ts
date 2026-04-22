/**
 * Returns the FastAPI base URL without a trailing slash.
 */
export function get_backend_base_url(): string {
  const raw = process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000"
  return raw.replace(/\/$/, "")
}
