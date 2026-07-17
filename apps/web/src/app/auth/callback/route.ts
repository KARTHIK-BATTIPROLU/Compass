import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const role = searchParams.get('role') || 'learner'
  
  if (code) {
    const supabase = await createClient()
    const { error, data } = await supabase.auth.exchangeCodeForSession(code)
    
    if (!error && data.user) {
      // Check if user already exists in the users table
      const { data: userRecord } = await supabase
        .from('users')
        .select('id')
        .eq('id', data.user.id)
        .single()
      
      if (!userRecord) {
        // User does not exist, meaning first login. 
        // Redirect to onboarding to capture region/language etc, and stamp role.
        return NextResponse.redirect(`${origin}/onboarding/${role}`)
      }
      
      // User exists, redirect to their main dashboard
      return NextResponse.redirect(`${origin}/${role}`)
    }
  }

  return NextResponse.redirect(`${origin}/login?error=auth_failed`)
}
