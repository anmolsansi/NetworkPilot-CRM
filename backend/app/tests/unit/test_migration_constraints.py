from pathlib import Path


def test_explicit_foreign_key_operations_are_named():
    versions = Path(__file__).parents[2] / "db" / "migrations" / "versions"
    migration_source = "\n".join(path.read_text() for path in versions.glob("*.py"))
    assert "create_foreign_key(None" not in migration_source
    assert "drop_constraint(None" not in migration_source
