"use server"

import { createClient } from "@/utils/supabase/server"
import { redirect } from "next/navigation"

export async function createLearnerSession() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error("Not authenticated")

  const { data, error } = await supabase.from("sessions").insert({
    user_id: user.id,
    title: "New Session",
  }).select("id").single()

  if (error) {
    console.error("Session error:", error)
    throw new Error("Failed to create session")
  }

  redirect(`/learn/chat/${data.id}`)
}
