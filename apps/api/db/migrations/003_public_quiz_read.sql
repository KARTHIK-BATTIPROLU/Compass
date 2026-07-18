-- Migration 003: allow public (anon) reads of open quizzes
--
-- Found while live-verifying migration 002 (DECISIONS.md DEC-024/DEC-025):
-- the public quiz page at /q/[token] reads `quizzes` directly via Supabase
-- with the anon key (no login — respondents are unauthenticated). Migration
-- 002 only gave SELECT to the owning teacher (quizzes_owner_select), so
-- once RLS was actually enforced, the public share-link page could no
-- longer read quiz data at all — a gap in the migration's own design, not
-- a regression of the original problem.
--
-- The `share_token` itself is the bearer secret (a hard-to-guess UUID) —
-- RLS can't restrict access "only when queried by the right token" (that's
-- an application-layer concept, not a row-level one), so this policy scopes
-- public reads to open quizzes only, matching what routers/quiz.py's
-- GET /api/quiz/{token} (service-key, no extra auth) already does today.

DROP POLICY IF EXISTS quizzes_public_read_open ON quizzes;
CREATE POLICY quizzes_public_read_open ON quizzes FOR SELECT USING (open = true);
