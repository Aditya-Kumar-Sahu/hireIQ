import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { TOKEN_COOKIE_NAME } from "@/lib/auth";

const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const token = cookies().get(TOKEN_COOKIE_NAME)?.value;

  if (!code || !state || !token) {
    return NextResponse.redirect(
      new URL("/settings?google=error&reason=missing_callback_context", request.url),
    );
  }

  const response = await fetch(`${API_BASE}/api/v1/integrations/google-calendar/callback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ code, state }),
    cache: "no-store",
  });

  if (!response.ok) {
    let reason = "connection_failed";
    try {
      const payload = (await response.json()) as { error?: string };
      if (payload.error) {
        reason = encodeURIComponent(payload.error);
      }
    } catch {
      reason = "connection_failed";
    }
    return NextResponse.redirect(new URL(`/settings?google=error&reason=${reason}`, request.url));
  }

  return NextResponse.redirect(new URL("/settings?google=connected", request.url));
}
