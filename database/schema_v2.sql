-- ============================================================
-- AIIA CTMS (AAYUR SATHI) — Database Schema V2
-- Expands from 9 tables to 14 tables per Master Technical Specification
-- Non-destructive additive migration
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- 1. Table: study_team (RBAC & Multi-Investigator Study Scoping)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_team (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id      UUID NOT NULL REFERENCES research_study(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role          VARCHAR(50) NOT NULL CHECK (role IN (
                  'pi', 'co_pi', 'coordinator', 'monitor', 'sub_investigator'
                )),
  assigned_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  assigned_by   UUID REFERENCES users(id),
  CONSTRAINT uq_study_team UNIQUE (study_id, user_id, role)
);

CREATE INDEX IF NOT EXISTS idx_study_team_study_id ON study_team(study_id);
CREATE INDEX IF NOT EXISTS idx_study_team_user_id ON study_team(user_id);

-- ------------------------------------------------------------
-- 2. Table: informed_consent (DPDP Act 2023 Consent Ledger / Gate 2)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS informed_consent (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id             UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  study_id               UUID NOT NULL REFERENCES research_study(id) ON DELETE CASCADE,
  consent_version        VARCHAR(50) NOT NULL,
  consented_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  withdrawn_at           TIMESTAMPTZ,
  withdrawal_reason      TEXT,
  consent_document_ref   VARCHAR(500),
  witnessed_by           UUID REFERENCES users(id),
  created_at             TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consent_patient_id ON informed_consent(patient_id);
CREATE INDEX IF NOT EXISTS idx_consent_study_id ON informed_consent(study_id);

-- ------------------------------------------------------------
-- 3. Table: data_query (GCP Clinical Data Query Engine)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_query (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id        UUID NOT NULL REFERENCES research_study(id) ON DELETE CASCADE,
  patient_id      UUID REFERENCES patient(id) ON DELETE SET NULL,
  visit_log_id    UUID REFERENCES visit_log(id) ON DELETE SET NULL,
  raised_by       UUID NOT NULL REFERENCES users(id),
  resolved_by     UUID REFERENCES users(id),
  field_name      VARCHAR(100) NOT NULL,
  query_text      TEXT NOT NULL,
  resolution_text TEXT,
  status          VARCHAR(30) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'answered', 'closed')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_data_query_study ON data_query(study_id);
CREATE INDEX IF NOT EXISTS idx_data_query_status ON data_query(status);

-- ------------------------------------------------------------
-- 4. Table: monitoring_visit (ALCOA+ Site Monitoring Reports)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monitoring_visit (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id             UUID NOT NULL REFERENCES research_study(id) ON DELETE CASCADE,
  monitor_id           UUID NOT NULL REFERENCES users(id),
  visit_date           DATE NOT NULL,
  visit_type           VARCHAR(50) NOT NULL CHECK (visit_type IN ('initiation', 'routine', 'for_cause', 'close_out')),
  findings             TEXT,
  issues_identified    TEXT,
  follow_up_required   BOOLEAN NOT NULL DEFAULT FALSE,
  report_submitted_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_monitoring_visit_study ON monitoring_visit(study_id);

-- ------------------------------------------------------------
-- 5. Table: ie_criteria (Study Inclusion/Exclusion Definitions)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ie_criteria (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id          UUID NOT NULL REFERENCES research_study(id) ON DELETE CASCADE,
  criterion_type    VARCHAR(20) NOT NULL CHECK (criterion_type IN ('inclusion', 'exclusion')),
  criterion_number  INT NOT NULL,
  description       TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_ie_criteria UNIQUE (study_id, criterion_type, criterion_number)
);

CREATE INDEX IF NOT EXISTS idx_ie_criteria_study ON ie_criteria(study_id);

-- ------------------------------------------------------------
-- 6. Table: ie_result (Patient Eligibility Assessment)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ie_result (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id     UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  criterion_id   UUID NOT NULL REFERENCES ie_criteria(id) ON DELETE CASCADE,
  met            BOOLEAN NOT NULL,
  evaluated_by   UUID REFERENCES users(id),
  evaluated_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_ie_result UNIQUE (patient_id, criterion_id)
);

CREATE INDEX IF NOT EXISTS idx_ie_result_patient ON ie_result(patient_id);

-- ------------------------------------------------------------
-- 7. Table: notifications (Cross-Role Alert Infrastructure)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       VARCHAR(255) NOT NULL,
  message     TEXT NOT NULL,
  severity    VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
  is_read     BOOLEAN NOT NULL DEFAULT FALSE,
  link        VARCHAR(255),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);

-- ------------------------------------------------------------
-- 8. Alter Existing Tables: Add Columns
-- ------------------------------------------------------------

-- adverse_event: WHO-UMC causality classification and actions
ALTER TABLE adverse_event
  ADD COLUMN IF NOT EXISTS causality VARCHAR(30) CHECK (
    causality IS NULL OR causality IN ('certain', 'probable', 'possible', 'unlikely', 'unclassified', 'unclassifiable')
  ),
  ADD COLUMN IF NOT EXISTS action_taken TEXT,
  ADD COLUMN IF NOT EXISTS reporter_role VARCHAR(50);

-- patient: ABDM Health ID (ABHA) integration
ALTER TABLE patient
  ADD COLUMN IF NOT EXISTS abha_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS abha_status VARCHAR(20) DEFAULT 'unverified';

-- research_study: Ayush formulation & classical literature references
ALTER TABLE research_study
  ADD COLUMN IF NOT EXISTS ayurvedic_intervention VARCHAR(255),
  ADD COLUMN IF NOT EXISTS ayush_system VARCHAR(50) DEFAULT 'Ayurveda',
  ADD COLUMN IF NOT EXISTS classical_reference VARCHAR(255);
