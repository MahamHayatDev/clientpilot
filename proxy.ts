import { NextRequest, NextResponse } from "next/server";

const USER = process.env.DASHBOARD_USER;
const PASSWORD = process.env.DASHBOARD_PASSWORD;

function unauthorized() {
  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="ClientPilot"' },
  });
}

export function proxy(request: NextRequest) {
  if (!USER || !PASSWORD) {
    return new NextResponse("Dashboard login is not configured", {
      status: 500,
    });
  }

  const header = request.headers.get("authorization");

  if (header?.startsWith("Basic ")) {
    try {
      const decoded = atob(header.slice(6));
      const index = decoded.indexOf(":");

      if (index >= 0) {
        const user = decoded.slice(0, index);
        const pass = decoded.slice(index + 1);

        if (user === USER && pass === PASSWORD) {
          return NextResponse.next();
        }
      }
    } catch {
      // Malformed header: fall through to unauthorized
    }
  }

  return unauthorized();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};