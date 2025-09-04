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


# --- Tests ---
@pytest.mark.parametrize("migration", get_migration_scripts())
def test_migration_upgrade_downgrade(alembic_cfg, migration):
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    try:
        command.upgrade(cfg, migration.revision)
        inspector = sa.inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        assert tables, "No tables created after upgrade"
        generated_keys = defaultdict(lambda: defaultdict(list))
        referenced_cols = get_referenced_columns_by_table(inspector)
        ordered_tables = get_insert_order(inspector)
        for table in ordered_tables:
            try:
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
        trans.rollback()
        conn.close()
        prev_rev = migration.down_revision or "base"
        command.downgrade(cfg, prev_rev)
        engine2 = create_engine(db_url)
        inspector = sa.inspect(engine2)
        tables_after = inspector.get_table_names()
        user_tables = [t for t in tables_after if t != "alembic_version"]
        if prev_rev == "base":
            assert not user_tables, "User tables not dropped after downgrade to base"
        engine2.dispose()
    finally:
        engine.dispose()


@pytest.mark.parametrize("migration", get_migration_scripts())
def test_migration_upgrade_downgrade_without_data(alembic_cfg, migration):
    cfg, db_url = alembic_cfg
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    try:
        command.upgrade(cfg, migration.revision)
        inspector = sa.inspect(engine)
        tables = inspector.get_table_names()
        assert tables, "No tables created after upgrade"
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
