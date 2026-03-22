import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { TOKEN_COOKIE_NAME } from "@/lib/auth";

const protectedPaths = ["/dashboard", "/jobs", "/candidates", "/applications", "/settings"];
const authPaths = ["/login", "/signup"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get(TOKEN_COOKIE_NAME)?.value;
  const { pathname } = request.nextUrl;

  const isProtected = protectedPaths.some((path) => pathname.startsWith(path));
  const isAuthPath = authPaths.some((path) => pathname.startsWith(path));

  if (isProtected && !token) {
    const url = new URL("/login", request.url);
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthPath && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/jobs/:path*",
    "/candidates/:path*",
    "/applications/:path*",
    "/settings/:path*",
    "/login",
    "/signup",
  ],
};
