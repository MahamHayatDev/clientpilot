import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300;

const BACKEND_URL = process.env.BACKEND_URL;
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

// The only backend routes the dashboard is allowed to reach.
const ALLOWED = ["companies", "drafts", "stats", "pipeline", "pipeline-batch"];

async function handler(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) {
  if (!BACKEND_URL || !BACKEND_API_KEY) {
    return NextResponse.json({ detail: "Server is not configured" }, { status: 500 });
  }

  const { path } = await ctx.params;
  if (!path?.length || !ALLOWED.includes(path[0])) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const target =
    `${BACKEND_URL.replace(/\/$/, "")}/` +
    path.map(encodeURIComponent).join("/") +
    req.nextUrl.search;

  const hasBody = !["GET", "HEAD"].includes(req.method);

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": BACKEND_API_KEY,
      },
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
    });

    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the backend. It may be waking up, so try again in a minute." },
      { status: 502 }
    );
  }
}

export { handler as GET, handler as POST, handler as PATCH };