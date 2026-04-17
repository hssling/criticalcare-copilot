"""Dataset builders. Each module writes a JSONL of
{ "task", "case", "target" [, "evidence"] } records ready for training.
Schema is enforced on ``case`` via safety.schema_validation.
"""
