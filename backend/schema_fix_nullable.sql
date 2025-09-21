-- Fix nullable constraints on manga_sessions table

ALTER TABLE manga_sessions ALTER COLUMN text DROP NOT NULL;
ALTER TABLE manga_sessions ALTER COLUMN title DROP NOT NULL;