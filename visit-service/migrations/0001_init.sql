CREATE TABLE IF NOT EXISTS clients_visits (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL,
    account_mgr_id BIGINT NOT NULL,
    visit_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    title VARCHAR(120) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_clients_visits_client_dt
    ON clients_visits (client_id, visit_datetime DESC);


CREATE TABLE IF NOT EXISTS clients_visits_evidence (
    id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT NOT NULL REFERENCES clients_visits(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_key VARCHAR(512) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_clients_visits_evidence_visit
    ON clients_visits_evidence (visit_id);