# AIIA CTMS — Database

PostgreSQL schema for the AIIA Clinical Trial Management System (Smart India
Hackathon build). FHIR R4-aligned. Source of truth: `AIIA_CTMS_Master_Context_v3`,
Section 7 — do not modify table shapes without updating that doc too.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | Full schema — 9 tables, immutability trigger, indexes |
| `drop_all.sql` | Tears everything down for a clean re-run in dev |
| `seeds/` | Synthetic seed data (Person 3's lane — see Section 10 of the master doc) |

## Tables

`users`, `research_study`, `patient`, `adverse_event`, `visit_log`,
`protocol_deviation`, `milestone`, `audit_trail`, `audit_anchor`.

`audit_trail` and `audit_anchor` are **insert-only** — a trigger
(`prevent_audit_modification`) blocks any `UPDATE` or `DELETE` at the database
level. This is load-bearing for the tamper-evidence demo (Section 8/14) —
don't remove it, even temporarily, to make debugging easier.

## Apply the schema

Requires PostgreSQL 13+ (for `gen_random_uuid()` via `pgcrypto`).

```bash
# Local Postgres
createdb aiia_ctms
psql -d aiia_ctms -f database/schema.sql

# Hosted (Railway / Render / Supabase) — use the connection string
# they give you:
psql "$DATABASE_URL" -f database/schema.sql
```

Reset during development:

```bash
psql "$DATABASE_URL" -f database/drop_all.sql
psql "$DATABASE_URL" -f database/schema.sql
```

## Notes

- `adverse_event.regulatory_deadline` is **computed in FastAPI before
  INSERT** (serious = report_date + 15 days, non-serious = +30 days) — not by
  a DB trigger. The `CHECK (regulatory_deadline > report_date)` constraint
  only guards against an obviously wrong value being written.
- `research_study.ctri_status != 'registered'` must be enforced as a
  **backend check** on the patient enrollment endpoint, not just a frontend
  validation (Section 5, Part A, Step 2 — legal hard gate).
- Indexes at the bottom of `schema.sql` aren't in the original locked spec
  but follow the FK/lookup patterns the API and dashboards will use — safe to
  drop if you want to stay byte-for-byte identical to Section 7.