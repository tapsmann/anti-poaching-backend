from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _migrate_columns(engine):
    """Add missing columns to existing tables."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    migrations = [
        ("rangers", "role", "TEXT NOT NULL DEFAULT 'ranger'"),
        ("rangers", "rank", "TEXT"),
        ("rangers", "specialization", "TEXT"),
        ("rangers", "assigned_area_id", "INTEGER"),
    ]
    for table, column, col_def in migrations:
        if table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            if column not in cols:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                    print(f"  Migrated: added {table}.{column}")
                except Exception as e:
                    print(f"  Migration skip {table}.{column}: {e}")

def init_db():
    import app.models
    try:
        with engine.begin() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            except Exception:
                print("PostGIS extension not available — continuing without it.")
        Base.metadata.create_all(bind=engine)
        _migrate_columns(engine)
        print("Database initialized successfully!")

        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        tables = inspector.get_table_names()
        if "rangers" in tables:
            from sqlalchemy.orm import Session
            with Session(bind=engine) as session:
                from app.models.ranger import Ranger
                count = session.query(Ranger).count()
                if count == 0:
                    print("No rangers found — running seed data...")
                    from seed_data import seed_database
                    seed_database()
                else:
                    print(f"Database has {count} rangers — skipping seed.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise