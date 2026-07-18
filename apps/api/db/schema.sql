-- LearnForge Postgres Schema (Supabase)

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role VARCHAR(50) NOT NULL CHECK (role IN ('faculty', 'learner')),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    region VARCHAR(100),
    language VARCHAR(50),
    standard VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    class_level VARCHAR(50),
    title VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    summary TEXT
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT,
    modes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'flow', 'script', 'slides', 'worksheet', 'quiz', 'flashcards',
        'resource_brief', 'resource_card', 'research_brief', 'diagram_gallery'
    )),
    content_md TEXT,
    export_urls JSONB,
    editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Curricula
CREATE TABLE IF NOT EXISTS curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    class_level VARCHAR(50),
    region VARCHAR(100),
    file_url TEXT,
    parsed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quizzes
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    share_token VARCHAR(100) UNIQUE,
    questions JSONB,
    open BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz Responses
CREATE TABLE IF NOT EXISTS quiz_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    respondent_name VARCHAR(255),
    answers JSONB,
    score FLOAT,
    per_topic JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics (Graph nodes)
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    subject VARCHAR(100),
    parent_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topic Edges (Graph edges)
CREATE TABLE IF NOT EXISTS topic_edges (
    parent_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    child_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    relation VARCHAR(100),
    PRIMARY KEY (parent_id, child_id)
);

-- User Topic Events
CREATE TABLE IF NOT EXISTS user_topic_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    kind VARCHAR(50) NOT NULL CHECK (kind IN ('studied', 'quizzed', 'weak')),
    score FLOAT,
    at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Weakness Profiles
CREATE TABLE IF NOT EXISTS weakness_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    mastery FLOAT CHECK (mastery >= 0 AND mastery <= 1),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, topic_id)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- Row-Level Security
--
-- The FastAPI backend talks to Supabase exclusively with SUPABASE_SERVICE_KEY,
-- which bypasses RLS entirely — these policies protect any DIRECT anon-key +
-- user-JWT access path (e.g. Next.js server actions / client components
-- hitting Supabase directly), not the FastAPI routes themselves. FastAPI-layer
-- ownership checks (agent/auth.py::user_owns_session) are a separate line of
-- defense. See db/migrations/002_rls_and_artifact_types.sql for the migration
-- that applies this to an already-live database, and DECISIONS.md DEC-016.
-- ═══════════════════════════════════════════════════════════════════════════

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

-- users: self only
CREATE POLICY users_select_self ON users FOR SELECT USING (id = auth.uid());
CREATE POLICY users_update_self ON users FOR UPDATE USING (id = auth.uid());
CREATE POLICY users_insert_self ON users FOR INSERT WITH CHECK (id = auth.uid());

-- sessions: owner
CREATE POLICY sessions_owner_select ON sessions FOR SELECT USING (user_id = auth.uid());
CREATE POLICY sessions_owner_insert ON sessions FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY sessions_owner_update ON sessions FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY sessions_owner_delete ON sessions FOR DELETE USING (user_id = auth.uid());

-- messages: owner via parent session
CREATE POLICY messages_owner_select ON messages FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = messages.session_id AND s.user_id = auth.uid())
);
CREATE POLICY messages_owner_insert ON messages FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = messages.session_id AND s.user_id = auth.uid())
);

-- artifacts: owner via parent session
CREATE POLICY artifacts_owner_select ON artifacts FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);
CREATE POLICY artifacts_owner_insert ON artifacts FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);
CREATE POLICY artifacts_owner_update ON artifacts FOR UPDATE USING (
    EXISTS (SELECT 1 FROM sessions s WHERE s.id = artifacts.session_id AND s.user_id = auth.uid())
);

-- curricula: owner
CREATE POLICY curricula_owner_all ON curricula FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- quizzes: owning teacher only, via artifact -> session -> user chain
CREATE POLICY quizzes_owner_select ON quizzes FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM artifacts a JOIN sessions s ON s.id = a.session_id
        WHERE a.id = quizzes.artifact_id AND s.user_id = auth.uid()
    )
);
-- No INSERT/UPDATE policy for anon/authenticated: quizzes are only ever
-- created by quiz_wf_node via the service-role client, which bypasses RLS.

-- Public share-link access: the /q/[token] page reads this directly via
-- Supabase with the anon key (respondents are never logged in). share_token
-- is the bearer secret; RLS can't scope "only when queried by the right
-- token" (that's application-layer), so this scopes public reads to open
-- quizzes only — the same access routers/quiz.py's GET /api/quiz/{token}
-- already grants via the service key.
CREATE POLICY quizzes_public_read_open ON quizzes FOR SELECT USING (open = true);

-- quiz_responses: owning teacher can read; public submit is server-mediated
CREATE POLICY quiz_responses_owner_select ON quiz_responses FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM quizzes q
        JOIN artifacts a ON a.id = q.artifact_id
        JOIN sessions s ON s.id = a.session_id
        WHERE q.id = quiz_responses.quiz_id AND s.user_id = auth.uid()
    )
);
-- No INSERT policy for anon/authenticated: the public /submit endpoint has no
-- end-user Supabase session (it's an unauthenticated public link) and writes
-- via the service-role client, which bypasses RLS. Intentional.

-- topics / topic_edges: readable by any authenticated user, service-role writes
CREATE POLICY topics_read_all ON topics FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY topic_edges_read_all ON topic_edges FOR SELECT USING (auth.role() = 'authenticated');

-- user_topic_events / weakness_profiles: self only
CREATE POLICY user_topic_events_self_select ON user_topic_events FOR SELECT USING (user_id = auth.uid());
CREATE POLICY weakness_profiles_self_select ON weakness_profiles FOR SELECT USING (user_id = auth.uid());
