import { cookies } from "next/headers";

import { TOKEN_COOKIE_NAME } from "@/lib/auth";

const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: { applicationId: string } },
) {
  const token = cookies().get(TOKEN_COOKIE_NAME)?.value;
  if (!token) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const response = await fetch(
    `${API_BASE}/api/v1/applications/${params.applicationId}/status`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    },
  );

  if (!response.ok || !response.body) {
    const errorText = await response.text();
    return new Response(errorText || "Unable to open status stream", {
      status: response.status,
    });
  }

  return new Response(response.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
