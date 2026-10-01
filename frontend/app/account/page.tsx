"use client";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import PageHeader from "../../components/PageHeader";
import { useAccount } from "../../components/AccountProvider";
import { accountRequest, syncAccount, type User } from "../../lib/account";
import { guestProgress, loadProgress, mergeProgress, saveProgress, setProgressOwner } from "../../lib/progress";

export default function AccountPage() {
  const { user, status, sync } = useAccount();
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [importGuest, setImportGuest] = useState(false);
  const [reauth, setReauth] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await accountRequest<{ user: User }>(`auth/${mode}`, "POST", { email, password });
      setProgressOwner(result.user.id);
      localStorage.setItem("attic.account", JSON.stringify(result.user));
      if (importGuest) saveProgress(mergeProgress(loadProgress(), guestProgress()));
      // A failed first sync must not discard a successful sign-in or imported progress.
      try { await syncAccount(result.user); } catch { /* provider retries on next page */ }
      window.location.assign("/progress");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not sign in."); setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError("");
    try {
      await sync();
      await accountRequest("auth/logout", "POST", {});
      localStorage.removeItem("attic.account");
      setProgressOwner(null);
      window.location.assign("/account");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not sign out."); setBusy(false); }
  }
  return <main className="shell narrowShell accountPage">
    <PageHeader title={user && !reauth ? "Your account" : "Save your learning progress"}>Keep your lessons, vocabulary reviews, test results, and study activity across devices.</PageHeader>
    {error && <p className="accountError" role="alert">{error}</p>}
    {user && !reauth ? <section className="card settingsFields">
      <h2>Signed in as {user.email}</h2>
      <p role="status">{status}</p>
      <div className="accountActions"><button disabled={busy} onClick={() => void sync()}>Sync now</button><Link href="/progress">View progress</Link></div>
      <h3>Import progress from this browser</h3>
      <p>If you studied here before creating an account, you can add that guest progress. Your saved account progress is merged with it.</p>
      <button className="secondary" disabled={busy} onClick={async () => { setBusy(true); saveProgress(mergeProgress(loadProgress(), guestProgress())); await sync(); setBusy(false); }}>Import guest progress</button>
      <p><Link href="/settings">Import a backup or an older sync code</Link></p>
      <div className="accountActions"><button className="secondary" disabled={busy} onClick={() => { setReauth(true); setMode("login"); setEmail(user.email); }}>Sign in again</button><button className="secondary" disabled={busy} onClick={logout}>Sign out</button></div>
    </section> : <section className="card">
      <div className="accountActions" aria-label="Account options"><button className={mode === "signup" ? "" : "secondary"} onClick={() => { setMode("signup"); setError(""); }}>Create account</button><button className={mode === "login" ? "" : "secondary"} onClick={() => { setMode("login"); setError(""); }}>Sign in</button></div>
      <h2>{mode === "signup" ? "Create your account" : "Sign in to your account"}</h2>
      <form className="settingsFields" onSubmit={submit}>
        <label>Email address<input type="email" autoComplete="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} required minLength={mode === "signup" ? 12 : 1} maxLength={256} value={password} onChange={e => setPassword(e.target.value)} aria-describedby="password-help" /></label>
        <p id="password-help">{mode === "signup" ? "Use at least 12 characters. Save your password in your password manager." : "Enter the password you used to create your account."}</p>
        <label className="accountCheck"><input type="checkbox" checked={importGuest} onChange={e => setImportGuest(e.target.checked)} /> Add guest progress saved in this browser</label>
        <button type="submit" disabled={busy}>{busy ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}</button>
      </form>
      <p><Link href="/learn">Continue learning as a guest</Link></p>
    </section>}
  </main>;
}
