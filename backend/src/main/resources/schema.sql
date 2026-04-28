CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    website_url TEXT,
    ideology VARCHAR(128),
    organization_type VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT organizations_name_unique UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS model_legislation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    title VARCHAR(500) NOT NULL,
    source_url TEXT,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS state_bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_code CHAR(2) NOT NULL,
    session VARCHAR(64) NOT NULL,
    bill_identifier VARCHAR(64) NOT NULL,
    title VARCHAR(500) NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT state_bills_state_code_uppercase CHECK (state_code = UPPER(state_code)),
    CONSTRAINT state_bills_natural_key UNIQUE (state_code, session, bill_identifier)
);

CREATE TABLE IF NOT EXISTS alignment_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_legislation_id UUID NOT NULL REFERENCES model_legislation(id) ON DELETE CASCADE,
    state_bill_id UUID NOT NULL REFERENCES state_bills(id) ON DELETE CASCADE,
    similarity_score DOUBLE PRECISION NOT NULL,
    matched_model_text TEXT NOT NULL,
    matched_bill_text TEXT NOT NULL,
    algorithm_used VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT alignment_matches_similarity_score_range
        CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_model_legislation_organization_id
    ON model_legislation (organization_id);

CREATE INDEX IF NOT EXISTS idx_model_legislation_source_url
    ON model_legislation (source_url);

CREATE INDEX IF NOT EXISTS idx_state_bills_lookup
    ON state_bills (state_code, session, bill_identifier);

CREATE INDEX IF NOT EXISTS idx_alignment_matches_model_legislation_id
    ON alignment_matches (model_legislation_id);

CREATE INDEX IF NOT EXISTS idx_alignment_matches_state_bill_id
    ON alignment_matches (state_bill_id);

CREATE INDEX IF NOT EXISTS idx_alignment_matches_similarity_score
    ON alignment_matches (similarity_score DESC);

DROP TRIGGER IF EXISTS trg_organizations_set_updated_at ON organizations;

CREATE TRIGGER trg_organizations_set_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_model_legislation_set_updated_at ON model_legislation;

CREATE TRIGGER trg_model_legislation_set_updated_at
    BEFORE UPDATE ON model_legislation
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_state_bills_set_updated_at ON state_bills;

CREATE TRIGGER trg_state_bills_set_updated_at
    BEFORE UPDATE ON state_bills
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_alignment_matches_set_updated_at ON alignment_matches;

CREATE TRIGGER trg_alignment_matches_set_updated_at
    BEFORE UPDATE ON alignment_matches
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
