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
    """Add missing columns to existing tables using raw SQL."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    migrations = [
        ("rangers", "role", "TEXT DEFAULT 'ranger'"),
        ("rangers", "rank", "TEXT"),
        ("rangers", "specialization", "TEXT"),
        ("rangers", "assigned_area_id", "INTEGER"),
        ("protected_areas", "zone_type", "TEXT"),
        ("protected_areas", "risk_level", "TEXT"),
        ("protected_areas", "size_hectares", "DOUBLE PRECISION"),
        ("protected_areas", "description", "TEXT"),
        ("protected_areas", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("incidents", "incident_type", "TEXT"),
        ("incidents", "severity", "TEXT"),
        ("community_reports", "report_type", "TEXT"),
        ("community_reports", "status", "TEXT DEFAULT 'pending'"),
        ("patrols", "patrol_type", "TEXT"),
        ("patrols", "status", "TEXT DEFAULT 'planned'"),
    ]
    for table, column, col_def in migrations:
        if table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            if column not in cols:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_def}'))
                    print(f"  Migrated: added {table}.{column}")
                except Exception as e:
                    print(f"  Migration skip {table}.{column}: {e}")

def _ensure_admin_user(engine):
    """Raw SQL guarantee that at least one admin user exists with correct password."""
    from app.core.security import get_password_hash
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    password_hash = get_password_hash("ranger123")

    admin_users = [
        ("Thandeka Ncube", "ZKW-001", "thandeka.ncube@zimparks.co.zw", "+263771000001", "admin", "commander", "quick_response"),
        ("Gift Muringani", "ZKW-128", "gift.muringani@zimparks.co.zw", "+263771000010", "admin", "commander", "quick_response"),
        ("Blessing Moyo", "ZKW-004", "blessing.moyo@zimparks.co.zw", "+263771000004", "ranger", "officer", "patrol"),
    ]

    with engine.begin() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM rangers"))
        count = result.scalar()

        if count == 0:
            print("  Inserting admin users via raw SQL...")
            for name, badge, email, phone, role, rank, spec in admin_users:
                try:
                    conn.execute(text("""
                        INSERT INTO rangers (name, badge_number, email, phone, role, rank, specialization, is_active, is_on_duty, password_hash, created_at, updated_at)
                        VALUES (:name, :badge, :email, :phone, :role, :rank, :spec, true, true, :pw, NOW(), NOW())
                        ON CONFLICT (badge_number) DO UPDATE SET
                            password_hash = EXCLUDED.password_hash,
                            role = EXCLUDED.role
                    """), {"name": name, "badge": badge, "email": email, "phone": phone, "role": role, "rank": rank, "spec": spec, "pw": password_hash})
                    print(f"    Ensured user: {email}")
                except Exception as e:
                    print(f"    Failed to insert {email}: {e}")
            print(f"  Admin users ready (password: ranger123)")
        else:
            print(f"  Database has {count} rangers.")
            for _, badge, email, phone, role, _, _ in admin_users:
                try:
                    conn.execute(text("""
                        UPDATE rangers SET password_hash = :pw, role = :role
                        WHERE badge_number = :badge
                    """), {"pw": password_hash, "role": role, "badge": badge})
                except Exception as e:
                    print(f"    Failed to update {email}: {e}")

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

        _ensure_admin_user(engine)

        try:
            from seed_data import seed_database
            seed_database()
        except Exception as e:
            print(f"Full seed failed (admin users already guaranteed): {e}")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
