"use server"

import { createClient } from "@/utils/supabase/server"
import { redirect } from "next/navigation"

export async function completeFacultyOnboarding(formData: FormData) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    throw new Error("Not authenticated")
  }
  
  const region = formData.get("region") as string
  const language = formData.get("language") as string
  
  const { error } = await supabase.from('users').insert({
    id: user.id,
    email: user.email,
    name: user.user_metadata?.full_name || user.email?.split('@')[0],
    role: 'faculty',
    region,
    language,
  })
  
  if (error) {
    console.error("Error creating faculty profile:", error)
    // We could return an error state here, but for now we'll just throw
    throw new Error("Failed to create profile")
  }
  
  redirect("/faculty")
}

export async function completeLearnerOnboarding(formData: FormData) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    throw new Error("Not authenticated")
  }
  
  const standard = formData.get("standard") as string
  
  const { error } = await supabase.from('users').insert({
    id: user.id,
    email: user.email,
    name: user.user_metadata?.full_name || user.email?.split('@')[0],
    role: 'learner',
    standard,
  })
  
  if (error) {
    console.error("Error creating learner profile:", error)
    throw new Error("Failed to create profile")
  }
  
  redirect("/learn")
}
