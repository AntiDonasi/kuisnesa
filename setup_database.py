#!/usr/bin/env python3
"""
Setup Database Script for KuisNesa - Enhanced with Auto-Migration
This script will:
1. Create all necessary tables in PostgreSQL database
2. Auto-detect missing columns
3. Auto-add missing columns to sync with models
4. Verify database schema matches models
"""

from database import Base, engine
from sqlalchemy import inspect, text, Column
import models
from typing import Dict, List, Set

def get_model_columns(model_class) -> Dict[str, Column]:
    """Get all columns from a SQLAlchemy model"""
    return {col.name: col for col in model_class.__table__.columns}

def get_database_columns(table_name: str) -> Set[str]:
    """Get all columns from database table"""
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
        return {col['name'] for col in columns}
    except Exception:
        return set()

def get_column_type_sql(column: Column) -> str:
    """Convert SQLAlchemy column type to SQL type"""
    col_type = str(column.type)

    # Map common types
    type_mapping = {
        'INTEGER': 'INTEGER',
        'VARCHAR': lambda: f'VARCHAR({column.type.length})' if hasattr(column.type, 'length') and column.type.length else 'VARCHAR(255)',
        'TEXT': 'TEXT',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP',
    }

    for key, value in type_mapping.items():
        if key in col_type.upper():
            return value() if callable(value) else value

    return 'TEXT'  # Default fallback

def detect_missing_columns() -> Dict[str, List[str]]:
    """Detect missing columns by comparing models with database"""
    print("\n🔍 Checking for missing columns...")

    missing_columns = {}

    # Define models to check
    models_to_check = {
        'users': models.User,
        'kuisioners': models.Kuisioner,
        'questions': models.Question,
        'responses': models.Response
    }

    for table_name, model_class in models_to_check.items():
        model_cols = get_model_columns(model_class)
        db_cols = get_database_columns(table_name)

        missing = set(model_cols.keys()) - db_cols

        if missing:
            missing_columns[table_name] = list(missing)
            print(f"   ⚠️  {table_name}: Missing {len(missing)} column(s): {', '.join(missing)}")
        else:
            print(f"   ✓ {table_name}: All columns present")

    return missing_columns

def add_missing_columns(missing_columns: Dict[str, List[str]]) -> bool:
    """Add missing columns to database tables"""
    if not missing_columns:
        print("\n✅ No missing columns - database is in sync!")
        return True

    print(f"\n🔧 Adding {sum(len(cols) for cols in missing_columns.values())} missing column(s)...")

    models_map = {
        'users': models.User,
        'kuisioners': models.Kuisioner,
        'questions': models.Question,
        'responses': models.Response
    }

    try:
        with engine.connect() as conn:
            for table_name, col_names in missing_columns.items():
                model_class = models_map[table_name]
                model_cols = get_model_columns(model_class)

                for col_name in col_names:
                    column = model_cols[col_name]
                    col_type = get_column_type_sql(column)

                    # Build ALTER TABLE statement
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = ""

                    # Add default value if exists
                    if column.default is not None:
                        if hasattr(column.default, 'arg'):
                            default_val = column.default.arg
                            if isinstance(default_val, str):
                                default = f"DEFAULT '{default_val}'"
                            elif isinstance(default_val, bool):
                                default = f"DEFAULT {str(default_val).upper()}"
                            else:
                                default = f"DEFAULT {default_val}"

                    # For nullable columns, don't add NOT NULL on creation
                    if column.nullable:
                        nullable = ""
                    else:
                        # Add NOT NULL only if there's a default or table is empty
                        nullable = ""

                    sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type} {default} {nullable}".strip()

                    print(f"   • Adding {table_name}.{col_name} ({col_type})")
                    conn.execute(text(sql))

                conn.commit()

        print("\n✅ All missing columns added successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error adding columns: {e}")
        return False

def verify_database() -> bool:
    """Verify database connection and structure"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = ['users', 'kuisioners', 'questions', 'responses']

        print("\n✅ Database Verification:")
        all_good = True

        for table in expected_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                print(f"   ✓ {table}: {len(columns)} columns")
            else:
                print(f"   ✗ {table}: MISSING")
                all_good = False

        return all_good

    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False

def print_detailed_schema():
    """Print detailed schema information"""
    print("\n📊 Complete Database Schema:\n")

    inspector = inspect(engine)
    tables = ['users', 'kuisioners', 'questions', 'responses']

    table_icons = {
        'users': '👥',
        'kuisioners': '📝',
        'questions': '❓',
        'responses': '💬'
    }

    for table in tables:
        if table not in inspector.get_table_names():
            continue

        columns = inspector.get_columns(table)
        print(f"{table_icons.get(table, '📋')} {table.upper()} ({len(columns)} columns):")

        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f", default={col['default']}" if col['default'] else ""
            print(f"   • {col['name']}: {col['type']} ({nullable}{default})")
        print()

def setup_database():
    """Main setup function with auto-migration"""
    print("=" * 70)
    print("🔧 KuisNesa Database Setup - Enhanced with Auto-Migration")
    print("=" * 70)
    print("\n📦 Step 1: Creating tables (if not exist)...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created/verified")

        # Detect missing columns
        print("\n📦 Step 2: Checking schema synchronization...")
        missing_columns = detect_missing_columns()

        # Add missing columns
        if missing_columns:
            print("\n📦 Step 3: Migrating database schema...")
            if not add_missing_columns(missing_columns):
                print("\n⚠️  Some columns could not be added. Manual intervention may be required.")
                return False
        else:
            print("\n📦 Step 3: Migration not needed - schema is up to date!")

        # Verify everything
        print("\n📦 Step 4: Final verification...")
        if not verify_database():
            print("\n⚠️  Verification failed. Please check the errors above.")
            return False

        # Print detailed schema
        print_detailed_schema()

        # Success message
        print("=" * 70)
        print("🎉 SUCCESS! Database is ready to use!")
        print("=" * 70)
        print("\n🚀 Next steps:")
        print("   1. Start the application:")
        print("      uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("\n   2. Access the application:")
        print("      https://kuisnesa.nauval.site")
        print("\n   3. Login with Google UNESA account")
        print("\n   4. Create kuisioner and enjoy 9 visualizations:")
        print("      • Bar Chart          • Pie Chart")
        print("      • Word Cloud         • Sentiment Analysis")
        print("      • Word Frequency     • Response Length")
        print("      • Top Contributors   • Keyword Analysis")
        print("      • Statistics Dashboard")
        print("\n📊 Text Analytics Features:")
        print("   • LDA Topic Modeling (3 topics)")
        print("   • TF-IDF Keyword Extraction (top 10)")
        print("   • Sentiment Analysis (positive/neutral/negative)")
        print("   • Comprehensive text statistics")
        print("\n💡 Features:")
        print("   ✓ Auto-detect missing columns")
        print("   ✓ Auto-migrate database schema")
        print("   ✓ Sync models with database")
        print("   ✓ No manual ALTER TABLE needed")
        print("\n💾 Database Schema:")
        print("   • users (5 fields) - with photo_url, unified role")
        print("   • kuisioners (10 fields) - with header_image, access control")
        print("   • questions (8 fields) - with required flag")
        print("   • responses (4 fields) - with unique constraint")
        print("\n📖 API Endpoints:")
        print("   GET  /kuisioner/{id}/stats      - HTML analytics page")
        print("   GET  /kuisioner/{id}/analytics  - JSON data")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n❌ Error setting up database:")
        print(f"   {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure PostgreSQL is running:")
        print("      sudo service postgresql start")
        print("\n   2. Check if database exists:")
        print("      psql -U postgres -c '\\l' | grep kuisioner")
        print("\n   3. Create database if needed:")
        print("      psql -U postgres")
        print("      CREATE DATABASE kuisioner_db OWNER kuisioner_user;")
        print("\n   4. Verify .env file has correct DATABASE_URL:")
        print("      postgresql://kuisioner_user:password@localhost:5432/kuisioner_db")
        print("\n   5. Test connection:")
        print("      python3 -c 'from database import engine; engine.connect()'")
        print("\n📖 For detailed setup instructions, see SETUP_DATABASE.md")

        import traceback
        traceback.print_exc()

        return False

if __name__ == "__main__":
    success = setup_database()
    exit(0 if success else 1)
