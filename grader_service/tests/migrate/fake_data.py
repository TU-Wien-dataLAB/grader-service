import os
import random
from collections import defaultdict, deque

import sqlalchemy as sa
from faker import Faker
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector


def get_insert_order(inspector: Inspector) -> list[str]:
    """
    Returns tables in order so that foreign key dependencies
    are respected (parents before children).
    """
    # filter alembic_version
    tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
    deps = defaultdict(set)  # table -> set of tables it depends on
    rev_deps = defaultdict(set)

    for table in tables:
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            parent = fk["referred_table"]
            deps[table].add(parent)
            rev_deps[parent].add(table)

    # Kahn’s algorithm (topological sort)
    order = []
    queue = deque([t for t in tables if not deps[t]])

    while queue:
        table = queue.popleft()
        order.append(table)
        for child in rev_deps[table]:
            deps[child].discard(table)
            if not deps[child]:
                queue.append(child)

    if len(order) != len(tables):
        raise RuntimeError("Cycle detected in foreign key dependencies!")

    return order


def generate_fake_row(
    table_name: str, inspector: sa.engine.reflection.Inspector, generated_keys: dict
) -> dict:
    """
    Generate a dictionary of fake data for inserting into a given table
    based on its schema, respecting foreign key constraints.
    """
    faker = Faker()
    columns = inspector.get_columns(table_name)
    fks = inspector.get_foreign_keys(table_name)
    row = {}

    # Map col_name -> (referred_table, referred_column)
    fk_map = {
        fk["constrained_columns"][0]: (fk["referred_table"], fk["referred_columns"][0])
        for fk in fks
    }

    for col in columns:
        col_name = col["name"]
        col_type = col["type"]
        nullable = col.get("nullable", True)

        # Skip autoincremented PK columns.
        # Note: autoincrement information is only available with PostgreSQL.
        # In sqlite, `col` will contain the "primary_key" key.
        if col.get("autoincrement") or (
            col.get("primary_key") and isinstance(col_type, sa.Integer) and col_name not in fk_map
        ):
            continue

        # Handle foreign keys first
        if col_name in fk_map:
            ref_table, ref_col = fk_map[col_name]
            if (
                ref_table in generated_keys
                and generated_keys[ref_table]
                and generated_keys[ref_table][ref_col]
            ):
                ref_table, ref_col = fk_map[col_name]
                # pick an existing PK - for integer IDs, it will be the last one added to the table,
                # to avoid integrity errors e.g. for submission logs/properties (a submission can only
                # have one of these), takepart (unique combination of user and lecture), etc.
                row[col_name] = max(generated_keys[ref_table][ref_col])
                continue
            elif isinstance(col_type, sa.Integer):
                # No PKs yet for this table → generate an integer placeholder
                row[col_name] = None if nullable else 1
                continue
            elif isinstance(col_type, sa.String):
                # No PKs yet for this table → generate a string placeholder
                row[col_name] = None if nullable else "fake_pk"
                continue

        # Integers
        if isinstance(col_type, sa.Integer):
            row[col_name] = random.randint(1, 1000)

        # PostgreSQL ENUM
        # is a special case of sa.String, therefore must be checked first
        elif isinstance(col_type, postgresql.ENUM):
            row[col_name] = random.choice(col_type.enums)

        # Strings
        elif isinstance(col_type, (sa.String, sa.Text)):
            length = getattr(col_type, "length", 20) or 20
            # special case for assignment settings
            if col_name == "settings":
                row[col_name] = "{}"
            else:
                row[col_name] = faker.text(max_nb_chars=min(length, 50)).lower()

        # Booleans
        elif isinstance(col_type, sa.Boolean):
            row[col_name] = random.choice([True, False])

        # Date / DateTime
        elif isinstance(col_type, sa.DateTime):
            row[col_name] = faker.date_time_this_decade()
        elif isinstance(col_type, sa.Date):
            row[col_name] = faker.date_this_decade()

        # Float / Numeric
        elif isinstance(col_type, (sa.Float, sa.Numeric)):
            row[col_name] = round(random.uniform(1, 1000), 2)

        # Binary
        elif isinstance(col_type, sa.LargeBinary):
            row[col_name] = os.urandom(16)

        # Fallback
        else:
            if col.get("default") is not None:
                # Fix default value for feedback_status
                row[col_name] = "not_generated"
            else:
                row[col_name] = faker.word().lower()

        # Handle NOT NULL
        if not nullable and row[col_name] is None:
            row[col_name] = faker.word()

    return row
