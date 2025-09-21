-- Schema expansion for chat and preview functionality
-- Add tables for session messages, phase previews, and real-time events

-- Session messages table for chat history
CREATE TABLE IF NOT EXISTS session_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'ai', 'system')),
    content TEXT NOT NULL,
    phase INTEGER CHECK (phase >= 1 AND phase <= 7),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Phase previews table for detailed phase progress and content
CREATE TABLE IF NOT EXISTS phase_previews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
    phase_number INTEGER NOT NULL CHECK (phase_number >= 1 AND phase_number <= 7),
    preview_type VARCHAR(20) NOT NULL CHECK (preview_type IN ('text', 'image', 'document')),
    content TEXT,
    image_url VARCHAR(500),
    document_url VARCHAR(500),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error', 'waiting_feedback')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, phase_number)
);

-- Session events table for WebSocket real-time updates
CREATE TABLE IF NOT EXISTS session_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_created_at ON session_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_session_messages_type ON session_messages(message_type);

CREATE INDEX IF NOT EXISTS idx_phase_previews_session_id ON phase_previews(session_id);
CREATE INDEX IF NOT EXISTS idx_phase_previews_phase_number ON phase_previews(phase_number);
CREATE INDEX IF NOT EXISTS idx_phase_previews_status ON phase_previews(status);

CREATE INDEX IF NOT EXISTS idx_session_events_session_id ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_session_events_created_at ON session_events(created_at);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);

-- Initialize phase previews for existing sessions
INSERT INTO phase_previews (session_id, phase_number, preview_type, status, progress)
SELECT
    id as session_id,
    phase_num,
    'text' as preview_type,
    CASE
        WHEN current_phase IS NULL OR phase_num > COALESCE(current_phase, 0) THEN 'pending'
        WHEN phase_num < COALESCE(current_phase, 0) THEN 'completed'
        WHEN phase_num = COALESCE(current_phase, 0) THEN
            CASE status
                WHEN 'completed' THEN 'completed'
                WHEN 'failed' THEN 'error'
                WHEN 'awaiting_feedback' THEN 'waiting_feedback'
                ELSE 'processing'
            END
        ELSE 'pending'
    END as status,
    CASE
        WHEN current_phase IS NULL OR phase_num > COALESCE(current_phase, 0) THEN 0
        WHEN phase_num < COALESCE(current_phase, 0) THEN 100
        WHEN phase_num = COALESCE(current_phase, 0) THEN
            CASE status
                WHEN 'completed' THEN 100
                WHEN 'failed' THEN 0
                WHEN 'awaiting_feedback' THEN 90
                ELSE 50
            END
        ELSE 0
    END as progress
FROM manga_sessions
CROSS JOIN generate_series(1, 7) as phase_num
ON CONFLICT (session_id, phase_number) DO NOTHING;

-- Add session messages for existing sessions
INSERT INTO session_messages (session_id, message_type, content, created_at)
SELECT
    id as session_id,
    'system' as message_type,
    CONCAT('セッション開始：', COALESCE(title, 'AI生成漫画')) as content,
    COALESCE(created_at, NOW()) as created_at
FROM manga_sessions
WHERE id NOT IN (SELECT DISTINCT session_id FROM session_messages WHERE message_type = 'system');

INSERT INTO session_messages (session_id, message_type, content, created_at)
SELECT
    id as session_id,
    'user' as message_type,
    COALESCE(text, '') as content,
    COALESCE(created_at, NOW()) + INTERVAL '1 second' as created_at
FROM manga_sessions
WHERE text IS NOT NULL AND text != ''
AND id NOT IN (SELECT DISTINCT session_id FROM session_messages WHERE message_type = 'user');

-- Update trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_session_messages_updated_at BEFORE UPDATE ON session_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_phase_previews_updated_at BEFORE UPDATE ON phase_previews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();