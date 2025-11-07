import os
from collections import defaultdict

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

from grader_service.tests.migrate.fake_data import generate_fake_row, get_insert_order

MIGRATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../migrate"))
ALEMBIC_INI = os.path.join(MIGRATE_DIR, "alembic.ini")


def get_migration_scripts():
    script_dir = ScriptDirectory(MIGRATE_DIR)
    return list(reversed([rev for rev in script_dir.walk_revisions()]))


# --- PostgreSQL test database management ---
@pytest.fixture(scope="session")
def postgres_server():
    """Start a temporary PostgreSQL server in Docker."""
    with PostgresContainer("postgres:17") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(params=["sqlite", "postgresql"])
def database_backend(request, tmp_path, postgres_server):
    """Use SQLite or a temporary PostgreSQL server."""
    if request.param == "sqlite":
        db_url = f"sqlite:///{tmp_path}/test.db"
    else:
        db_url = postgres_server
    return request.param, db_url


# autouse param ensures that this fixture is run for each test
@pytest.fixture(autouse=True)
def clean_database(database_backend):
    """Ensure each test starts with a clean database schema."""
    backend, db_url = database_backend
    if backend == "postgresql":
        engine = sa.create_engine(db_url)
        with engine.begin() as conn:
            conn.execute(sa.text("DROP SCHEMA public CASCADE;"))
            conn.execute(sa.text("CREATE SCHEMA public;"))
        engine.dispose()
    elif backend == "sqlite":
        # SQLite uses a new file per test, so it does not need cleaning
        pass
    yield


@pytest.fixture
def alembic_cfg(database_backend):
    backend, db_url = database_backend
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", MIGRATE_DIR)
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg, db_url


def get_referenced_columns_by_table(inspector):
    refd = defaultdict(set)
    for t in inspector.get_table_names():
        if t == "alembic_version":
            continue
        for fk in inspector.get_foreign_keys(t):
            rt = fk.get("referred_table")
            rcols = fk.get("referred_columns") or []
            for rc in rcols:
                refd[rt].add(rc)
    return refd


def get_table_data(engine, tables):
    """Return a dict of table_name -> list of rows as dicts"""
    metadata = sa.MetaData()
    metadata.reflect(bind=engine, only=tables)
    data = {}
    for table in tables:
        tbl = metadata.tables[table]
        with engine.connect() as conn:
            result = conn.execute(sa.select(tbl))
            data[table] = [dict(r) for r in result.mappings()]
    return data


def normalize_type(col_type):
    """Normalize SQLAlchemy type string."""
    t = str(col_type).upper()
    # Collapse common aliases
    if t.startswith("VARCHAR("):
        return "VARCHAR"  # ignore length differences
    if t in ("INT", "INTEGER", "BIGINT"):
        return "INTEGER"
    if t.startswith("DATETIME"):
        return "DATETIME"
    if t.startswith("TIMESTAMP"):
        return "TIMESTAMP"
    return t


def get_schema_snapshot(inspector, exclude_tables=("alembic_version",)):
    """Capture a normalized schema snapshot for stable comparisons."""
    snapshot = {}
    for table in sorted(inspector.get_table_names()):
        if table in exclude_tables:
            continue
        cols = inspector.get_columns(table)
        pks = inspector.get_pk_constraint(table)
        fks = inspector.get_foreign_keys(table)
        indexes = inspector.get_indexes(table)
        # Normalize columns
        norm_cols = sorted(
            [
                (
                    c["name"],
                    normalize_type(c["type"]),
                    bool(c.get("nullable", True)),
                    str(c.get("default")) if c.get("default") is not None else None,
                )
                for c in cols
            ],
            key=lambda x: x[0],
        )
        # Normalize PKs
        norm_pks = sorted(pks.get("constrained_columns", []))
        # Normalize FKs
        norm_fks = sorted(
            [
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in fks
            ],
            key=lambda x: (x[1], x[0]),
        )
        # Normalize Indexes
        norm_indexes = sorted(
            [
                (ix["name"], tuple(sorted(ix["column_names"])), bool(ix.get("unique", False)))
                for ix in indexes
            ],
            key=lambda x: x[0],
        )
        snapshot[table] = {
            "columns": norm_cols,
            "primary_keys": norm_pks,
            "foreign_keys": norm_fks,
            "indexes": norm_indexes,
        }

    return snapshot


# --- Tests ---
@pytest.mark.parametrize("migration", get_migration_scripts())
def test_migration_upgrade_downgrade(alembic_cfg, migration):
    """Upgrades to the n-th migration, adds a column to each table
    and then downgrades back to the previous revision.
    """
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    try:
        # Upgrade the database schema
        command.upgrade(cfg, migration.revision)
        inspector = sa.inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        assert tables, "No tables created after upgrade"

        # Track generated keys for foreign key relationships
        generated_keys = defaultdict(lambda: defaultdict(list))
        referenced_cols = get_referenced_columns_by_table(inspector)
        # Identify the order in which tables should be populated based on foreign key relationships
        ordered_tables = get_insert_order(inspector)

        for table in ordered_tables:
            try:
                # Insert one row into the table
                metadata = sa.MetaData()
                metadata.reflect(bind=engine, only=[table])
                tbl = metadata.tables[table]
                row = generate_fake_row(table, inspector, generated_keys)
                with engine.begin() as conn:
                    conn.execute(tbl.insert().values(**row))

                    # Save ANY columns that other tables FK to
                    for col in referenced_cols.get(table, []):
                        if col in row and row[col] is not None:
                            generated_keys[table][col].append(row[col])
            except Exception:
                raise Exception(f"Failed to insert into table {table}")

        # Commit the transaction
        trans.commit()
        conn.close()

        # Downgrade to the previous revision
        prev_rev = migration.down_revision or "base"
        command.downgrade(cfg, prev_rev)
        engine2 = create_engine(db_url)
        inspector = sa.inspect(engine2)
        tables_after = inspector.get_table_names()
        user_tables = [t for t in tables_after if t != "alembic_version"]
        if prev_rev == "base":
            assert not user_tables, "User tables not dropped after downgrade to base"
    finally:
        engine.dispose()
        engine2.dispose()


@pytest.mark.parametrize("migration", get_migration_scripts())
def test_migration_upgrade_downgrade_without_data(alembic_cfg, migration):
    """Upgrades to the n-th migration and then downgrades back to the previous revision."""
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    try:
        # Upgrade the database schema
        command.upgrade(cfg, migration.revision)
        inspector = sa.inspect(engine)
        tables = inspector.get_table_names()
        assert tables, "No tables created after upgrade"

        # Downgrade to the previous revision
        prev_rev = migration.down_revision or "base"
        command.downgrade(cfg, prev_rev)
        inspector = sa.inspect(engine)
        tables_after = inspector.get_table_names()
        user_tables = [t for t in tables_after if t != "alembic_version"]
        if prev_rev == "base":
            assert not user_tables, "User tables not dropped after downgrade to base"
    finally:
        trans.rollback()
        conn.close()
        engine.dispose()


def test_migration_full_upgrade_and_downgrade_chain_without_data(alembic_cfg):
    """Test the full upgrade and downgrade chain without data."""
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    try:
        for migration in get_migration_scripts():
            command.upgrade(cfg, migration.revision)
        inspector = sa.inspect(engine)
        tables = inspector.get_table_names()
        assert tables, "No tables after full upgrade chain"
        command.downgrade(cfg, "base")
        inspector = sa.inspect(engine)
        tables_after = inspector.get_table_names()
        user_tables = [t for t in tables_after if t != "alembic_version"]
        assert not user_tables, "User tables not dropped after full downgrade chain"
    finally:
        trans.rollback()
        conn.close()
        engine.dispose()


@pytest.mark.parametrize("migration", get_migration_scripts())
def test_migration_upgrade_downgrade_with_data_from_prev_revision(alembic_cfg, migration):
    """Checks for data integrity during migration upgrade and downgrade.
    Steps:
    1. Upgrade the database to the (n-1)-th migration.
    2. Add a new row to each table.
    3. Upgrade the database to the n-th migration.
    4. Perform data integrity checks after the upgrade.
    5. Downgrade the database back to the (n-1)-th migration.
    6. Perform data integrity checks after the downgrade.
    """
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()

    # Check if the migration has a down_revision
    # if not, skip the test
    if migration.down_revision is None:
        return
    try:
        # Upgrade the database schema to (n-1) migration
        command.upgrade(cfg, migration.down_revision)
        inspector = sa.inspect(engine)
        schema_before_upgrade = get_schema_snapshot(inspector)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        assert tables, "No tables created after upgrade"

        # Track generated keys for foreign key relationships
        generated_keys = defaultdict(lambda: defaultdict(list))
        referenced_cols = get_referenced_columns_by_table(inspector)
        # Identify the order in which tables should be populated based on foreign key relationships
        ordered_tables = get_insert_order(inspector)

        for table in ordered_tables:
            try:
                # Insert one row into the table
                metadata = sa.MetaData()
                metadata.reflect(bind=engine, only=[table])
                tbl = metadata.tables[table]
                row = generate_fake_row(table, inspector, generated_keys)
                with engine.begin() as conn:
                    conn.execute(tbl.insert().values(**row))

                    # Save ANY columns that other tables FK to
                    for col in referenced_cols.get(table, []):
                        if row.get(col) is not None:
                            generated_keys[table][col].append(row[col])
            except Exception:
                raise Exception(f"Failed to insert into table {table}")

        data_before_upgrade = get_table_data(engine, tables)

        # Upgrade the database schema to n-th migration
        command.upgrade(cfg, migration.revision)
        # Check if the migration this something
        engine2 = create_engine(db_url)
        inspector = sa.inspect(engine2)
        tables_after_upgrade = [t for t in inspector.get_table_names() if t != "alembic_version"]
        data_after_upgrade = get_table_data(engine2, tables_after_upgrade)
        assert data_before_upgrade != data_after_upgrade, "Data did not changed after upgrade!"

        # Commit the transaction
        trans.commit()
        conn.close()

        # Downgrade to the previous revision
        prev_rev = migration.down_revision or "base"
        command.downgrade(cfg, prev_rev)
        engine3 = create_engine(db_url)
        inspector3 = sa.inspect(engine3)
        schema_after_downgrade = get_schema_snapshot(inspector3)
        tables_after_downgrade = [t for t in inspector3.get_table_names() if t != "alembic_version"]
        if prev_rev == "base":
            assert not tables_after_downgrade, "User tables not dropped after downgrade to base"
        else:
            # Check schema consistency
            try:
                assert schema_before_upgrade == schema_after_downgrade, (
                    f"Schema changed after downgrade from {migration.revision} ({migration.doc}) "
                    f"to {prev_rev}!"
                )
            except AssertionError as e:
                if migration.revision != "fc5d2febe781":
                    # Migration "fc5d2febe781"
                    # ("merged assignment configuration options into assignment settings column"):
                    # The `allow_files` default differs; before upgrade the default was `None` (!),
                    # although the column is not nullable. In the downgrade function, the server_default
                    # is set to "f".
                    raise e
            # Check if the data is still the same
            data_after_downgrade = get_table_data(engine2, tables_after_downgrade)

            data_loss_migrations = (
                "f1ae66d52ad9",  # remove group table
                "fc5d2febe781",  # merged assignment configuration options into assignment settings
            )
            try:
                assert data_before_upgrade == data_after_downgrade, (
                    f"Data changed after downgrade from {migration.revision} ({migration.doc}) "
                    f"to {prev_rev}!"
                )
            except AssertionError as e:
                # If the tested migration is part of the not lossless migration do not throw the error
                if migration.revision not in data_loss_migrations:
                    raise e
    finally:
        engine.dispose()
        engine2.dispose()
        engine3.dispose()
