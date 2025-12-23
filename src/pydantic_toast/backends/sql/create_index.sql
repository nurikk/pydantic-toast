-- Create index on class_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_external_models_class_name
ON external_models(class_name);
