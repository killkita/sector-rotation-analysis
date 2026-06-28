# scripts/create_schema.py

import os
from sqlalchemy import (
    create_engine, Column, Integer, Float, 
    String, Date, ForeignKey, MetaData, Table
)

# ── 1. Connect to SQLite database ────────────────────────────────────────────
engine = create_engine(
    f"sqlite:///{os.path.expanduser('~/sector-rotation-analysis/data/sector_data.db')}"
)
metadata = MetaData()

# ── 2. Define the SECTORS table ───────────────────────────────────────────────
# This is the master reference table - one row per sector
sectors = Table("sectors", metadata,
    Column("sector_id",  Integer, primary_key=True, autoincrement=True),
    Column("ticker",     String,  nullable=False, unique=True),
    Column("name",       String,  nullable=False),
    Column("category",   String,  nullable=False),  # defensive / cyclical
)

# ── 3. Define the PRICES table ────────────────────────────────────────────────
# One row per sector per date - links back to sectors via sector_id
prices = Table("prices", metadata,
    Column("price_id",   Integer, primary_key=True, autoincrement=True),
    Column("sector_id",  Integer, ForeignKey("sectors.sector_id"), nullable=False),
    Column("date",       Date,    nullable=False),
    Column("close",      Float,   nullable=False),
    Column("volume",     Float,   nullable=True),
    Column("return_1m",  Float,   nullable=True),  # monthly return %
)

# ── 4. Define the INDICATORS table ────────────────────────────────────────────
# One row per date - macroeconomic data from FRED
indicators = Table("indicators", metadata,
    Column("indicator_id",  Integer, primary_key=True, autoincrement=True),
    Column("date",          Date,    nullable=False, unique=True),
    Column("fed_funds_rate", Float,  nullable=True),
    Column("yield_curve",   Float,   nullable=True),  # 10yr minus 2yr spread
    Column("unemployment",  Float,   nullable=True),
    Column("cpi",           Float,   nullable=True),
)

# ── 5. Define the RECESSIONS table ───────────────────────────────────────────
# One row per recession period - NBER official dates
recessions = Table("recessions", metadata,
    Column("recession_id",  Integer, primary_key=True, autoincrement=True),
    Column("start_date",    Date,    nullable=False),
    Column("end_date",      Date,    nullable=False),
    Column("label",         String,  nullable=False),  # e.g. "2008 Financial Crisis"
)

# ── 6. Create all tables in the database ─────────────────────────────────────
metadata.create_all(engine)

print("✓ Database schema created successfully")
print("\nTables created:")
for table in metadata.sorted_tables:
    print(f"  - {table.name} ({len(table.columns)} columns)")