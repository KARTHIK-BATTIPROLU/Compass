# Decisions Log

## Phase 1
- **Onboarding form extra fields**: `TODO.md` requested fields like `subjects` for faculty, and `branch/field`, `goal` for learners. However, the database schema provided in `CONTEXT.md` §8 (`users` table) does not have these columns. Since `CONTEXT.md` dictates making the smallest reasonable decision and noting it here, I have included these fields in the UI forms but they are currently ignored during the database insertion to avoid altering the fixed schema. They can be added to a JSONB `metadata` column later if needed.
