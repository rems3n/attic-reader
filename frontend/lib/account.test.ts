import { beforeEach, describe, expect, it, vi } from "vitest";
import { emptyProgress, loadProgress, saveProgress, setProgressOwner, guestProgress, mergeProgress } from "./progress";
import { syncAccount } from "./account";
const values = new Map<string,string>();
beforeEach(() => {
  values.clear(); setProgressOwner(null);
  const storage = { getItem: (k:string) => values.get(k) ?? null, setItem: (k:string,v:string) => values.set(k,v) };
  vi.stubGlobal("localStorage", storage);
  vi.stubGlobal("window", { localStorage: storage, dispatchEvent: vi.fn() });
});
describe("account progress", () => {
  it("isolates guest and different account caches", () => {
    const guest = emptyProgress(); guest.course.track = "myth"; saveProgress(guest);
    setProgressOwner("a"); expect(loadProgress().course.track).toBeUndefined();
    const a = emptyProgress(); a.course.track = "history"; saveProgress(a);
    setProgressOwner("b"); expect(loadProgress().course.track).toBeUndefined();
    expect(guestProgress().course.track).toBe("myth");
    setProgressOwner("a"); expect(loadProgress().course.track).toBe("history");
  });
  it("keeps lessons and review days from both devices without duplicate counts", () => {
    const a = emptyProgress(), b = emptyProgress();
    a.course.lessons.a = {status:"done", best:1, attempts:1, updated:20};
    b.course.lessons.b = {status:"done", best:1, attempts:1, updated:30};
    b.course.lessons.a = {status:"open", best:0, attempts:0, updated:10};
    a.log = [{day:"2026-10-01",reviews:5,newCards:2}];
    b.log = [{day:"2026-10-01",reviews:3,newCards:1},{day:"2026-09-30",reviews:2,newCards:1}];
    const merged = mergeProgress(a,b);
    expect(merged.course.lessons.a.status).toBe("done");
    expect(merged.course.lessons.b.status).toBe("done");
    expect(merged.log.map(x=>x.reviews)).toEqual([2,5]);
  });
  it("loads settings on a new device and retries conflicting writes", async () => {
    setProgressOwner("a");
    const remote = emptyProgress(); remote.settings.sessionSize = 40;
    const reply = (data:unknown,status=200) => new Response(JSON.stringify(data),{status});
    const fetch = vi.fn().mockResolvedValueOnce(reply({document:remote,revision:1})).mockResolvedValueOnce(reply({detail:"Conflict"},409)).mockResolvedValueOnce(reply({document:remote,revision:2})).mockResolvedValueOnce(reply({saved_at:1}));
    vi.stubGlobal("fetch",fetch);
    await syncAccount({id:"a",email:"a@example.com"});
    expect(fetch).toHaveBeenCalledTimes(4);
    expect(loadProgress().settings.sessionSize).toBe(40);
    expect(JSON.parse(fetch.mock.calls[3][1].body).revision).toBe(2);
  });
});
