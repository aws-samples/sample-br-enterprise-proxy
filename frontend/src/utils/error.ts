export function extractErrorMessage(
  error: unknown,
  fallback = 'Operation failed',
): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: { detail?: string } } })
      .response;
    return resp?.data?.detail || fallback;
  }
  return fallback;
}
