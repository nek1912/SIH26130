-- supabase/migrations/006_documents_extraction_status.sql
-- Add extraction_status column to documents table for background extraction tracking.

-- Add extraction_status as TEXT (not enum) to documents table
-- The enum type already exists from migration 003 but is used on document_requirements
ALTER TABLE documents ADD COLUMN extraction_status TEXT DEFAULT 'pending';
