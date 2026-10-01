import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const PATHS = new Set(["auth/signup", "auth/login", "auth/logout", "me", "me/progress"]);

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path.join("/");
  if (!PATHS.has(path)) return new NextResponse(null, { status: 404 });
  if (request.method !== "GET") {
    const origin = request.headers.get("origin");
    const host = request.headers.get("host");
    if (!origin || new URL(origin).host !== host || request.headers.get("x-attic-request") !== "1") {
      return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
    }
  }
  const body = request.method === "GET" ? undefined : await request.text();
  if (body && new TextEncoder().encode(body).length > 2.1 * 1024 * 1024) return new NextResponse(null, { status: 413 });
  try {
    const upstream = await fetch(`${BASE}/api/${path}`, {
      method: request.method, body, cache: "no-store", signal: AbortSignal.timeout(20000),
      headers: {
        "Content-Type": "application/json", "X-Attic-Request": "1",
        Cookie: request.headers.get("cookie") ?? "",
        "X-Attic-User": request.headers.get("x-attic-user") ?? "",
      },
    });
    const response = new NextResponse(await upstream.text(), { status: upstream.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
    for (const cookie of upstream.headers.getSetCookie()) response.headers.append("Set-Cookie", cookie);
    return response;
  } catch {
    return NextResponse.json({ detail: "Account service is unavailable. Your progress is saved on this device." }, { status: 503 });
  }
}
export { proxy as GET, proxy as POST, proxy as PUT };
