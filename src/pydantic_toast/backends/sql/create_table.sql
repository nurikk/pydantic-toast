-- Create external_models table for storing Pydantic model data
CREATE TABLE IF NOT EXISTS external_models (
    id UUID PRIMARY KEY,
    class_name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
