"use server"

import { createClient } from "@/utils/supabase/server"
import { redirect } from "next/navigation"

export async function createFacultySession(formData: FormData) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error("Not authenticated")

  const classLevel = formData.get("class_level") as string
  const title = `New ${classLevel} Session`

  const { data, error } = await supabase.from("sessions").insert({
    user_id: user.id,
    class_level: classLevel,
    title,
  }).select("id").single()

  if (error) {
    console.error("Session error:", error)
    throw new Error("Failed to create session")
  }

  redirect(`/faculty/chat/${data.id}`)
}
