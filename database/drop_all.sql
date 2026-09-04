-- ============================================================
-- AIIA CTMS — Drop all tables (dev/reset use only)
-- Run this before re-running schema.sql if you need a clean slate.
-- Order matters: children before parents (FK dependencies).
-- ============================================================

DROP TABLE IF EXISTS audit_anchor CASCADE;
DROP TABLE IF EXISTS audit_trail CASCADE;
DROP TABLE IF EXISTS milestone CASCADE;
DROP TABLE IF EXISTS protocol_deviation CASCADE;
DROP TABLE IF EXISTS visit_log CASCADE;
DROP TABLE IF EXISTS adverse_event CASCADE;
DROP TABLE IF EXISTS patient CASCADE;
DROP TABLE IF EXISTS research_study CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP FUNCTION IF EXISTS prevent_audit_modification() CASCADE;