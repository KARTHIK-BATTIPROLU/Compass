-- Migration 002: Row-Level Security + artifacts.type CHECK fix
-- Run this against the live Supabase project (SQL Editor or psql). schema.sql
-- has also been updated so a fresh install includes this from the start.
--
-- Context: the FastAPI backend (apps/api) talks to Supabase exclusively with
-- SUPABASE_SERVICE_KEY, which bypasses RLS entirely — these policies protect
-- any DIRECT anon-key + user-JWT access path (e.g. Next.js server actions /
-- client components hitting Supabase directly), not the FastAPI routes
-- themselves. FastAPI-layer ownership checks (agent/auth.py::user_owns_session)
-- are a separate, already-fixed line of defense (see DECISIONS.md DEC-015).

-- ── Fix: artifacts.type CHECK never matched what the code actually emits ────
-- diagrams_wf/research_wf/resource_wf write 'diagram_gallery', 'research_brief',
-- 'resource_card' — none of which were in the original CHECK list, so every
-- one of those inserts violated the constraint and was silently dropped by
-- composer.py's try/except. See VERIFICATION.md "Final Sprint — Harness Run 1".
ALTER TABLE artifacts DROP CONSTRAINT IF EXISTS artifacts_type_check;
ALTER TABLE artifacts ADD CONSTRAINT artifacts_type_check CHECK (
    type IN (
        'flow', 'script', 'slides', 'worksheet', 'quiz', 'flashcards',
        'resource_brief', 'resource_card', 'research_brief', 'diagram_gallery'
    )
);

-- ── Enable RLS ────────────────────────────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE curricula ENABLE ROW LEVEL SECURITY;
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_topic_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE weakness_profiles ENABLE ROW LEVEL SECURITY;

-- ── users: self only ─────────────────────────────────────────────────────
DROP POLICY IF EXISTS users_select_self ON users;
CREATE POLICY users_select_self ON users FOR SELECT USING (id = auth.uid());
DROP POLICY IF EXISTS users_update_self ON users;
CREATE POLICY users_update_self ON users FOR UPDATE USING (id = auth.uid());
DROP POLICY IF EXISTS users_insert_self ON users;
CREATE POLICY users_insert_self ON users FOR INSERT WITH CHECK (id = auth.uid());

-- ── sessions: owner ──────────────────────────────────────────────────────
DROP POLICY IF EXISTS sessions_owner_select ON sessions;
CREATE POLICY sessions_owner_select ON sessions FOR SELECT USING (user_id = auth.uid());
DROP POLICY IF EXISTS sessions_owner_insert ON sessions;
CREATE POLICY sessions_owner_insert ON sessions FOR INSERT WITH CHECK (user_id = auth.uid());
DROP POLICY IF EXISTS sessions_owner_update ON sessions;
CREATE POLICY sessions_owner_update ON sessions FOR UPDATE USING (user_id = auth.uid());
DROP POLICY IF EXISTS sessions_owner_delete ON sessions;
CREATE POLICY sessions_owner_delete ON sessions FOR DELETE USING (user_id = auth.uid());

-- ── messages: owner via parent session ───────────────────────────────────
DROP POLICY IF EXISTS messages_owner_select ON messages;
CREATE POLICY messages_owner_select ON messages FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = messages.session_id AND s.user_id = auth.uid())
);
DROP POLICY IF EXISTS messages_owner_insert ON messages;
CREATE POLICY messages_owner_insert ON messages FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = messages.session_id AND s.user_id = auth.uid())
);

-- ── artifacts: owner via parent session ──────────────────────────────────
DROP POLICY IF EXISTS artifacts_owner_select ON artifacts;
CREATE POLICY artifacts_owner_select ON artifacts FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);
DROP POLICY IF EXISTS artifacts_owner_insert ON artifacts;
CREATE POLICY artifacts_owner_insert ON artifacts FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);
DROP POLICY IF EXISTS artifacts_owner_update ON artifacts;
CREATE POLICY artifacts_owner_update ON artifacts FOR UPDATE USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);

-- ── curricula: owner ─────────────────────────────────────────────────────
DROP POLICY IF EXISTS curricula_owner_all ON curricula;
CREATE POLICY curricula_owner_all ON curricula FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ── quizzes: owning teacher only, via artifact -> session -> user chain ──
-- (artifact_id now reliably points at a real artifacts row — see DEC-014)
DROP POLICY IF EXISTS quizzes_owner_select ON quizzes;
CREATE POLICY quizzes_owner_select ON quizzes FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM artifacts a JOIN sessions s ON s.id = a.session_id
        WHERE a.id = quizzes.artifact_id AND s.user_id = auth.uid()
    )
);
-- No INSERT/UPDATE policy for anon/authenticated: quizzes are only ever
-- created by quiz_wf_node via the service-role client, which bypasses RLS.

-- ── quiz_responses: owning teacher can read; public submit is server-mediated ─
DROP POLICY IF EXISTS quiz_responses_owner_select ON quiz_responses;
CREATE POLICY quiz_responses_owner_select ON quiz_responses FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM quizzes q
        JOIN artifacts a ON a.id = q.artifact_id
        JOIN sessions s ON s.id = a.session_id
        WHERE q.id = quiz_responses.quiz_id AND s.user_id = auth.uid()
    )
);
-- No INSERT policy for anon/authenticated: routers/quiz.py's public /submit
-- endpoint writes via the service-role client (no end-user Supabase session
-- exists on that path — it's an unauthenticated public link), which bypasses
-- RLS. This is intentional, not an oversight.

-- ── topics / topic_edges: readable by any authenticated user, service-role writes ─
DROP POLICY IF EXISTS topics_read_all ON topics;
CREATE POLICY topics_read_all ON topics FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS topic_edges_read_all ON topic_edges;
CREATE POLICY topic_edges_read_all ON topic_edges FOR SELECT USING (auth.role() = 'authenticated');

-- ── user_topic_events / weakness_profiles: self only ─────────────────────
DROP POLICY IF EXISTS user_topic_events_self_select ON user_topic_events;
CREATE POLICY user_topic_events_self_select ON user_topic_events FOR SELECT USING (user_id = auth.uid());
DROP POLICY IF EXISTS weakness_profiles_self_select ON weakness_profiles;
CREATE POLICY weakness_profiles_self_select ON weakness_profiles FOR SELECT USING (user_id = auth.uid());
