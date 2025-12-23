-- Upsert (insert or update) model data
INSERT INTO external_models (
    id, class_name, data, schema_version, created_at, updated_at
)
VALUES ($1, $2, $3, $4, $5, $5)
ON CONFLICT (id) DO UPDATE
SET data = EXCLUDED.data,
    updated_at = EXCLUDED.updated_at;
