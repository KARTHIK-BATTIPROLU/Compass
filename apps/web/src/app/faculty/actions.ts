"use server"

import { createClient } from "@/utils/supabase/server"
import { createClient as createRawClient } from "@supabase/supabase-js"
import { redirect } from "next/navigation"

export async function createFacultySession(formData: FormData) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error("Not authenticated")

  const classLevel = formData.get("class_level") as string
  const title = `New ${classLevel} Session`

  // Bypass RLS completely for inserts
  const adminClient = createRawClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  // Ensure user exists in public.users to satisfy foreign key constraints
  await adminClient.from("users").upsert({
    id: user.id,
    email: user.email || "unknown@demo.com",
    role: "faculty",
    name: user.email?.split("@")[0] || "Faculty"
  })

  const { data, error } = await adminClient.from("sessions").insert({
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
