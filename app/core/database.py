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

def _run_sql(engine, sql, params=None):
    """Run a single SQL statement in its own transaction."""
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def _migrate_columns(engine):
    """Convert ENUM/geometry columns to TEXT — one statement per transaction."""
    cols_to_text = [
        ("rangers", "role"),
        ("rangers", "rank"),
        ("rangers", "specialization"),
        ("protected_areas", "zone_type"),
        ("protected_areas", "risk_level"),
        ("incidents", "incident_type"),
        ("incidents", "severity"),
        ("community_reports", "report_type"),
        ("community_reports", "status"),
        ("patrols", "patrol_type"),
        ("patrols", "status"),
    ]
    for table, column in cols_to_text:
        try:
            result = engine.connect().execute(text(
                "SELECT udt_name FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ), {"t": table, "c": column})
            row = result.fetchone()
            result.close()
            if row and row[0] != "text":
                _run_sql(engine, f'ALTER TABLE {table} ALTER COLUMN {column} TYPE TEXT')
                print(f"  Converted {table}.{column} to TEXT")
        except Exception as e:
            print(f"  Skip {table}.{column}: {e}")

    geo_cols = [
        ("rangers", "base_location"),
        ("rangers", "current_location"),
        ("rangers", "last_known_location"),
    ]
    for table, column in geo_cols:
        try:
            result = engine.connect().execute(text(
                "SELECT udt_name FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ), {"t": table, "c": column})
            row = result.fetchone()
            result.close()
            if row and row[0] != "text":
                try:
                    _run_sql(engine, f'ALTER TABLE {table} ALTER COLUMN {column} TYPE TEXT USING ST_AsText({column})')
                except Exception:
                    _run_sql(engine, f'ALTER TABLE {table} ALTER COLUMN {column} TYPE TEXT')
                print(f"  Converted {table}.{column} to TEXT (from geometry)")
        except Exception as e:
            print(f"  Skip {table}.{column}: {e}")

    try:
        _run_sql(engine, "ALTER TABLE patrols ALTER COLUMN route DROP NOT NULL")
        print("  Made patrols.route nullable")
    except Exception:
        pass

def _ensure_admin_user(engine):
    """UPSERT admin users via raw SQL — always runs."""
    from app.core.security import get_password_hash
    password_hash = get_password_hash("ranger123")

    admin_users = [
        ("Thandeka Ncube", "ZKW-001", "thandeka.ncube@zimparks.co.zw", "+263771000001", "admin"),
        ("Gift Muringani", "ZKW-128", "gift.muringani@zimparks.co.zw", "+263771000010", "admin"),
        ("Blessing Moyo", "ZKW-004", "blessing.moyo@zimparks.co.zw", "+263771000004", "ranger"),
    ]

    print("  Ensuring admin users...")
    for name, badge, email, phone, role in admin_users:
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO rangers (name, badge_number, email, phone, role, is_active, is_on_duty, password_hash, created_at, updated_at)
                    VALUES (:name, :badge, :email, :phone, :role, true, true, :pw, NOW(), NOW())
                    ON CONFLICT (email) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role,
                        badge_number = EXCLUDED.badge_number
                """), {"name": name, "badge": badge, "email": email, "phone": phone, "role": role, "pw": password_hash})
            print(f"    OK: {email}")
        except Exception as e:
            print(f"    FAIL {email}: {e}")
    print(f"  Users ready (password: ranger123)")

def init_db():
    import app.models
    try:
        _migrate_columns(engine)
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully!")

        _ensure_admin_user(engine)

        try:
            from seed_data import seed_database
            seed_database()
        except Exception as e:
            print(f"ORM seed partially failed (admin users guaranteed): {e}")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
