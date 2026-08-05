/** Simulates network/AI processing latency for mock services. */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Generates a reasonably unique id for mock records created client-side. */
export function generateId(prefix = "id"): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
