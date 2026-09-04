-- ============================================================
-- AIIA CTMS — Database Schema
-- Source: AIIA_CTMS_Master_Context_v3, Section 7 ("Locked")
-- All tables FHIR R4-aligned. Build exactly as written — do not
-- retrofit FHIR alignment later.
-- ============================================================

-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- Table: users
-- ------------------------------------------------------------
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(255) NOT NULL,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          VARCHAR(50) NOT NULL CHECK (role IN (
                  'pi','coordinator','monitor',
                  'ethics_committee','pharmacovigilance',
                  'admin','regulator')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: research_study (FHIR ResearchStudy aligned)
-- ------------------------------------------------------------
CREATE TABLE research_study (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title                     VARCHAR(500) NOT NULL,
  status                    VARCHAR(50) NOT NULL,
  phase                     VARCHAR(50),
  sponsor                   VARCHAR(255),
  ctri_registration_number  VARCHAR(100),
  ctri_status               VARCHAR(50) DEFAULT 'not_registered',
  iec_approval_status       VARCHAR(50) DEFAULT 'pending',
  iec_approval_date         DATE,
  iec_renewal_due           DATE,
  enrollment_target         INT NOT NULL,
  enrolled_count            INT NOT NULL DEFAULT 0
    CHECK (enrolled_count <= enrollment_target),
  site_id                   VARCHAR(100),
  principal_investigator_id UUID REFERENCES users(id),
  start_date                DATE,
  end_date                  DATE,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: patient (FHIR Patient aligned)
-- ------------------------------------------------------------
CREATE TABLE patient (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id              UUID NOT NULL REFERENCES research_study(id),
  screening_number      VARCHAR(50) NOT NULL,
  randomization_number  VARCHAR(50),
  enrollment_date       DATE,
  status                VARCHAR(50) CHECK (status IN (
                          'screened','enrolled','completed',
                          'withdrawn','screen_failed')),
  age                   INT,
  sex                   VARCHAR(10),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: adverse_event (FHIR AdverseEvent aligned)
-- ------------------------------------------------------------
CREATE TABLE adverse_event (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id             UUID NOT NULL REFERENCES research_study(id),
  patient_id           UUID NOT NULL REFERENCES patient(id),
  description          TEXT NOT NULL,
  seriousness          VARCHAR(20) CHECK (seriousness IN
                         ('serious','non_serious')),
  outcome              VARCHAR(100),
  onset_date           DATE,
  report_date          DATE NOT NULL,
  -- regulatory_deadline is COMPUTED IN FASTAPI BEFORE INSERT, not by a DB
  -- trigger: serious = report_date + 15 days, non_serious = +30 days
  regulatory_deadline  DATE NOT NULL
    CHECK (regulatory_deadline > report_date),
  reported_by          UUID REFERENCES users(id),
  status               VARCHAR(30) CHECK (status IN (
                         'open','under_review','resolved','reported')),
  ae_term              VARCHAR(255), -- synthetic MedDRA stub
  created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: visit_log
-- ------------------------------------------------------------
CREATE TABLE visit_log (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id       UUID NOT NULL REFERENCES research_study(id),
  patient_id     UUID NOT NULL REFERENCES patient(id),
  visit_number   INT NOT NULL,
  scheduled_date DATE NOT NULL,
  actual_date    DATE,
  status         VARCHAR(30) CHECK (status IN (
                   'scheduled','completed','missed','overdue')),
  deviation_flag BOOLEAN NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: protocol_deviation
-- ------------------------------------------------------------
CREATE TABLE protocol_deviation (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id     UUID NOT NULL REFERENCES research_study(id),
  patient_id   UUID NOT NULL REFERENCES patient(id),
  visit_log_id UUID REFERENCES visit_log(id),
  description  TEXT NOT NULL,
  severity     VARCHAR(20) CHECK (severity IN
                 ('minor','major','critical')),
  reported_by  UUID REFERENCES users(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: milestone
-- ------------------------------------------------------------
CREATE TABLE milestone (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id       UUID NOT NULL REFERENCES research_study(id),
  milestone_type VARCHAR(60) CHECK (milestone_type IN (
                   'iec_approval','ctri_registration',
                   'site_activation','first_patient_enrolled',
                   'last_patient_enrolled','database_lock',
                   'study_closeout','iec_renewal')),
  due_date       DATE NOT NULL,
  completed_date DATE,
  status         VARCHAR(20) CHECK (status IN
                   ('pending','completed','overdue')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: audit_trail — INSERT ONLY, NEVER UPDATE OR DELETE
-- ------------------------------------------------------------
CREATE TABLE audit_trail (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id),
  action      VARCHAR(50) NOT NULL,
    -- values: CREATE, UPDATE, DELETE_ATTEMPT, LOGIN,
    --         LOGOUT, STATUS_CHANGE, EXPORT, AE_REPORT
  entity_type VARCHAR(60) NOT NULL,
    -- values: research_study, patient, adverse_event,
    --         visit_log, milestone, user
  entity_id   UUID,
  old_value   JSONB,
  new_value   JSONB,
  row_hash    VARCHAR(64) NOT NULL,
    -- SHA-256 hex of previous audit_trail row's content
    -- first row uses SHA-256("GENESIS")
  timestamp   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Block any UPDATE or DELETE on audit_trail
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_trail is immutable. No modifications allowed.';
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER audit_trail_immutable
BEFORE UPDATE OR DELETE ON audit_trail
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- ------------------------------------------------------------
-- Table: audit_anchor — INSERT ONLY (blockchain commit ledger)
-- ------------------------------------------------------------
CREATE TABLE audit_anchor (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_start_id      UUID REFERENCES audit_trail(id),
  batch_end_id        UUID REFERENCES audit_trail(id),
  row_count           INT NOT NULL,
  merkle_root         VARCHAR(64) NOT NULL,
  chain               VARCHAR(50) NOT NULL DEFAULT 'polygon-amoy-testnet',
  tx_hash             VARCHAR(100),
  block_number        BIGINT,
  committed_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  verification_status VARCHAR(20) DEFAULT 'pending'
    CHECK (verification_status IN ('pending','matched','mismatched'))
);

-- Same immutability trigger applied to audit_anchor
CREATE TRIGGER audit_anchor_immutable
BEFORE UPDATE OR DELETE ON audit_anchor
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- ------------------------------------------------------------
-- Recommended indexes (not in the locked spec, but standard
-- practice for the FK/lookup patterns every role dashboard
-- and API route will hit — safe to include, easy to drop)
-- ------------------------------------------------------------
CREATE INDEX idx_patient_study_id            ON patient(study_id);
CREATE INDEX idx_adverse_event_study_id       ON adverse_event(study_id);
CREATE INDEX idx_adverse_event_patient_id     ON adverse_event(patient_id);
CREATE INDEX idx_adverse_event_status         ON adverse_event(status);
CREATE INDEX idx_visit_log_study_id           ON visit_log(study_id);
CREATE INDEX idx_visit_log_patient_id         ON visit_log(patient_id);
CREATE INDEX idx_protocol_deviation_study_id  ON protocol_deviation(study_id);
CREATE INDEX idx_milestone_study_id           ON milestone(study_id);
CREATE INDEX idx_audit_trail_entity           ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_trail_timestamp        ON audit_trail(timestamp);
CREATE INDEX idx_research_study_pi_id         ON research_study(principal_investigator_id);