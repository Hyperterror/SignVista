import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_PATHS = new Set(['/', '/auth']);

/**
 * Route guard: pages other than the landing and auth pages require the
 * HttpOnly session cookie. The backend still validates every request; this
 * just avoids rendering protected pages for signed-out visitors.
 */
export function middleware(request: NextRequest) {
    const { pathname, search } = request.nextUrl;
    if (PUBLIC_PATHS.has(pathname)) {
        return NextResponse.next();
    }
    if (!request.cookies.get('access_token')) {
        const url = request.nextUrl.clone();
        url.pathname = '/auth';
        url.search = `?next=${encodeURIComponent(pathname + search)}`;
        return NextResponse.redirect(url);
    }
    return NextResponse.next();
}

export const config = {
    // Skip API proxying, Next internals, sign media and any file with an extension
    matcher: ['/((?!api|_next|assets|health|favicon.ico|.*\\..*).*)'],
};
