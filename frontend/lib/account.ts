import { loadProgress, saveProgress, migrateProgress, mergeProgress, progressKey, type Progress } from "./progress";
export type User = { id: string; email: string };
export class AccountError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function accountRequest<T>(path: string, method = "GET", body?: unknown, user?: string): Promise<T> {
  const response = await fetch(`/api/account/${path}`, { method, credentials: "same-origin", signal: AbortSignal.timeout(12000), cache: "no-store", headers: { "Content-Type": "application/json", "X-Attic-Request": "1", ...(user ? { "X-Attic-User": user } : {}) }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new AccountError(typeof data.detail === "string" ? data.detail : "Unable to complete the request. Check your details and try again.", response.status);
  return data;
}
export async function syncAccount(user: User): Promise<void> {
  const key = progressKey();
  const hasLocal = localStorage.getItem(key) !== null;
  for (let attempt = 0; attempt < 3; attempt++) {
    const remote = await accountRequest<{ document: Progress | null; revision: number }>("me/progress", "GET", undefined, user.id);
    const local = loadProgress();
    if (progressKey() !== key) return;
    const merged = remote.document ? (hasLocal ? mergeProgress(local, migrateProgress(remote.document)) : migrateProgress(remote.document)) : local;
    // A sync code is a legacy backup credential and must stay on the device.
    const document = { ...merged, settings: { ...merged.settings, syncCode: "" } };
    try {
      const result = await accountRequest<{ saved_at: number }>("me/progress", "PUT", { document, revision: remote.revision }, user.id);
      // Keep any work completed while the upload was in flight.
      if (progressKey() !== key) return;
      saveProgress({ ...(hasLocal ? mergeProgress(loadProgress(), merged) : merged), lastSync: result.saved_at * 1000 });
      return;
    } catch (error) {
      if (!(error instanceof AccountError) || error.status !== 409 || attempt === 2) throw error;
    }
  }
}
