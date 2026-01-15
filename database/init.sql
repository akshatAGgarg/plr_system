-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Structural Snapshots
CREATE TABLE IF NOT EXISTS page_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(255) NOT NULL,
    route_id VARCHAR(255) NOT NULL,
    simhash VARCHAR(255),
    dom_structure JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookup by build/route
CREATE INDEX idx_snapshots_build_route ON page_snapshots(build_id, route_id);


-- 2. Locator Registry
CREATE TABLE IF NOT EXISTS locator_registry (
    locator_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_file_path VARCHAR(512) NOT NULL,
    locator_key VARCHAR(255) NOT NULL, -- e.g., "login_button"
    current_selector VARCHAR(1024) NOT NULL,
    stability_score FLOAT DEFAULT 1.0, -- Adaptive weighting: 1.0 = stable, < 1.0 = unstable
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Locator History (Audit Trail)
CREATE TABLE IF NOT EXISTS locator_history (
    id SERIAL PRIMARY KEY,
    locator_id UUID REFERENCES locator_registry(locator_id),
    old_selector VARCHAR(1024),
    new_selector VARCHAR(1024),
    change_reason VARCHAR(255), -- "RTED", "Semantic", "Manual"
    confidence_score FLOAT,
    build_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
