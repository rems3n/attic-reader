"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { accountRequest, AccountError, syncAccount, type User } from "../lib/account";
import { setProgressOwner } from "../lib/progress";

const Context = createContext<{ user: User | null; status: string; sync: () => Promise<void> }>({ user: null, status: "", sync: async () => {} });
export const useAccount = () => useContext(Context);
export default function AccountProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [status, setStatus] = useState("");
  const busy = useRef(false);
  const current = useRef<User | null>(null);
  const sync = async () => {
    if (!current.current || busy.current) return;
    busy.current = true;
    setStatus("Saving progress…");
    try { await syncAccount(current.current); setStatus("Progress saved"); }
    catch (error) { setStatus(error instanceof AccountError && error.status === 401 ? "Session expired. Sign in to sync." : "Saved on this device. Sync will retry when connected."); }
    finally { busy.current = false; }
  };
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const changed = () => { if (!busy.current) { clearTimeout(timer); timer = setTimeout(() => void sync(), 1500); } };
    const otherTab = (event: StorageEvent) => { if (event.key === "attic.account") window.location.reload(); };
    const resume = () => { if (document.visibilityState === "visible") void sync(); };
    void (async () => {
      let account: User | null = null;
      try { account = (await accountRequest<{ user: User }>("me")).user; }
      catch (error) {
        // Retain an account's local work offline or after session expiry; never treat it as guest work.
        try { account = JSON.parse(localStorage.getItem("attic.account") ?? "null"); } catch { /* no cache */ }
        if (account) setStatus(error instanceof AccountError && error.status === 401 ? "Session expired. Sign in to sync." : "Offline. Progress is saved on this device.");
      }
      if (stopped) return;
      current.current = account;
      setProgressOwner(account?.id ?? null);
      setUser(account);
      if (account) {
        localStorage.setItem("attic.account", JSON.stringify(account));
        await sync();
      }
      if (!stopped) setReady(true);
    })();
    window.addEventListener("attic-progress", changed);
    window.addEventListener("online", resume);
    window.addEventListener("storage", otherTab);
    document.addEventListener("visibilitychange", resume);
    const periodic = setInterval(() => void sync(), 60000);
    return () => { stopped = true; clearTimeout(timer); clearInterval(periodic); window.removeEventListener("attic-progress", changed); window.removeEventListener("online", resume); window.removeEventListener("storage", otherTab); document.removeEventListener("visibilitychange", resume); };
  }, []);
  return <Context.Provider value={{ user, status, sync }}>{ready ? children : <main className="shell"><p role="status">Loading your progress…</p></main>}</Context.Provider>;
}
