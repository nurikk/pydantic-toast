-- Select model data by id and class_name
SELECT data FROM external_models
WHERE id = $1 AND class_name = $2;
