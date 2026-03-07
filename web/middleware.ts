import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes that don't need auth
  const publicPaths = ['/login', '/api', '/_next', '/favicon.ico'];
  if (publicPaths.some((path) => pathname.startsWith(path)) || pathname === '/') {
    return NextResponse.next();
  }

  // Check for auth cookie (access_token set by FastAPI)
  const accessToken = request.cookies.get('access_token');
  if (!accessToken?.value && pathname.startsWith('/admin')) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
