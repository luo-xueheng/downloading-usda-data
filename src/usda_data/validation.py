"""Shared validation entry point."""
def validate(frame, schema):
    """Return strictly typed observations; reject missing dimensions and duplicate keys."""
    return schema.validate(frame)
