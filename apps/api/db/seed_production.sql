-- Seed data for production database

-- 1. Insert some default topics
INSERT INTO topics (id, name) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Cardiac Cycle'),
    ('00000000-0000-0000-0000-000000000002', 'Photosynthesis'),
    ('00000000-0000-0000-0000-000000000003', 'Transformer Architectures'),
    ('00000000-0000-0000-0000-000000000004', 'Cellular Respiration')
ON CONFLICT (name) DO NOTHING;

-- 2. Insert some dummy curriculum files for testing
-- Note: actual user_id needs to be mapped to whoever uses the system, 
-- but these can be public or owned by a dummy user if RLS allows public read.
