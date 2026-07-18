import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  const isAuthRoute = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/auth')
  const isProtected = request.nextUrl.pathname.startsWith('/faculty') || request.nextUrl.pathname.startsWith('/learn') || request.nextUrl.pathname.startsWith('/onboarding')
  
  if (!user && isProtected && !isAuthRoute) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Role guarding
  if (user && isProtected && !request.nextUrl.pathname.startsWith('/onboarding')) {
    const { data: userRecord } = await supabase.from('users').select('role').eq('id', user.id).single()
    if (userRecord) {
      if (request.nextUrl.pathname.startsWith('/faculty') && userRecord.role !== 'faculty') {
         return NextResponse.redirect(new URL('/learn', request.url))
      }
      if (request.nextUrl.pathname.startsWith('/learn') && userRecord.role !== 'learner') {
         return NextResponse.redirect(new URL('/faculty', request.url))
      }
    }
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
