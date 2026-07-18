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
    type VARCHAR(50) NOT NULL CHECK (type IN ('flow', 'script', 'slides', 'worksheet', 'quiz', 'flashcards', 'resource_brief')),
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
