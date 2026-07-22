'use server'

import { createClient as createServerClient } from '@/utils/supabase/server'
import { createClient as createSupabaseClient } from '@supabase/supabase-js'

const adminAuthClient = createSupabaseClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

export async function login(formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string

  const supabase = await createServerClient()
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return { error: error.message }
  }

  return { success: true }
}

export async function signup(formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string
  const role = formData.get('role') as string || 'learner'

  // 1. Create the user using the admin API to bypass email confirmation
  const { data, error: createError } = await adminAuthClient.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
    user_metadata: { role }
  })

  if (createError) {
    if (!createError.message.includes('already exists')) {
      return { error: createError.message }
    }
  } else if (data.user) {
    // 2. Also ensure user record exists in public.users
    const supabase = await createServerClient()
    await supabase.from('users').upsert({
      id: data.user.id,
      role: role,
    }, { onConflict: 'id' })
  }

  // 3. Log them in using standard auth to set the session cookies
  const supabase = await createServerClient()
  const { error: signInError } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (signInError) {
    return { error: signInError.message }
  }

  return { success: true }
}
