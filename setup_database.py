#!/usr/bin/env python3
"""
Setup Database Script for KuisNesa
This script will create all necessary tables in PostgreSQL database
Updated for enhanced version with text analytics and visualizations
"""

from database import Base, engine
from sqlalchemy import inspect
import models

def print_table_structure():
    """Print detailed table structure after creation"""
    inspector = inspect(engine)

    print("\n📊 Database Structure Details:\n")

    # Users table
    print("👥 USERS Table:")
    print("   Fields:")
    print("   • id (Integer, Primary Key)")
    print("   • nama (String, 100)")
    print("   • email (String, 120, Unique, Indexed)")
    print("   • role (String, 20, default='user') - Unified role for all users")
    print("   • photo_url (String, 500, Nullable) - Google profile photo")
    print("   Relationships:")
    print("   • One-to-Many with Kuisioners (owner)")
    print("   • One-to-Many with Responses")

    print("\n📝 KUISIONERS Table:")
    print("   Fields:")
    print("   • id (Integer, Primary Key)")
    print("   • title (String, 200, Required)")
    print("   • description (Text)")
    print("   • background (String, 200, default='white')")
    print("   • theme (String, 50, default='light')")
    print("   • header_image (String, 300) - NEW: Header image URL")
    print("   • start_date (DateTime, default=now)")
    print("   • end_date (DateTime, Nullable)")
    print("   • access (String, 20, default='public')")
    print("   • owner_id (Integer, Foreign Key → users.id)")
    print("   Relationships:")
    print("   • Many-to-One with User (owner)")
    print("   • One-to-Many with Questions")

    print("\n❓ QUESTIONS Table:")
    print("   Fields:")
    print("   • id (Integer, Primary Key)")
    print("   • kuisioner_id (Integer, Foreign Key → kuisioners.id)")
    print("   • text (Text, Required)")
    print("   • qtype (String, 50, default='short_text')")
    print("   • options (Text) - JSON string for multiple choice")
    print("   • media_url (String, 300) - Image/video URL")
    print("   • required (Boolean, default=False) - NEW: Required field flag")
    print("   Relationships:")
    print("   • Many-to-One with Kuisioner")
    print("   • One-to-Many with Responses")

    print("\n💬 RESPONSES Table:")
    print("   Fields:")
    print("   • id (Integer, Primary Key)")
    print("   • answer (Text, Required)")
    print("   • user_id (Integer, Foreign Key → users.id)")
    print("   • question_id (Integer, Foreign Key → questions.id)")
    print("   Relationships:")
    print("   • Many-to-One with User")
    print("   • Many-to-One with Question")
    print("   Constraints:")
    print("   • Unique constraint on (user_id, question_id) - Prevents duplicates")

def verify_database():
    """Verify database connection and structure"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = ['users', 'kuisioners', 'questions', 'responses']

        print("\n✅ Database Verification:")
        for table in expected_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                print(f"   ✓ {table}: {len(columns)} columns")
            else:
                print(f"   ✗ {table}: MISSING")
                return False

        return True
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False

def setup_database():
    """Create all tables in the database"""
    print("=" * 60)
    print("🔧 KuisNesa Database Setup")
    print("=" * 60)
    print("\n📦 Creating database tables...")
    print("   Models: User, Kuisioner, Question, Response")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("\n✅ Database setup completed successfully!")
        print("\n📋 Tables created:")
        print("   - users (with photo_url and unified role)")
        print("   - kuisioners (with header_image and access control)")
        print("   - questions (with required field flag)")
        print("   - responses (with unique constraint)")

        # Print detailed structure
        print_table_structure()

        # Verify creation
        if verify_database():
            print("\n" + "=" * 60)
            print("🎉 SUCCESS! Database is ready to use!")
            print("=" * 60)
            print("\n🚀 Next steps:")
            print("   1. Start the application:")
            print("      uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
            print("\n   2. Access the application:")
            print("      http://localhost:8000")
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
            print("\n💡 API Endpoint:")
            print("   GET /kuisioner/{id}/analytics - JSON data")
            print("=" * 60)

    except Exception as e:
        print("\n❌ Error setting up database:")
        print(f"   {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure PostgreSQL is running:")
        print("      sudo service postgresql start")
        print("\n   2. Check if database exists:")
        print("      psql -U postgres -c '\\l' | grep kuisioner")
        print("\n   3. Create database if needed:")
        print("      createdb -U kuisioner_user kuisioner_db")
        print("\n   4. Verify .env file has correct DATABASE_URL:")
        print("      postgresql://kuisioner_user:password@localhost:5432/kuisioner_db")
        print("\n   5. Check user permissions:")
        print("      psql -U postgres")
        print("      GRANT ALL PRIVILEGES ON DATABASE kuisioner_db TO kuisioner_user;")
        print("\n   6. Test connection:")
        print("      psql -U kuisioner_user -d kuisioner_db -c 'SELECT version();'")
        print("\n📖 For detailed setup instructions, see SETUP_DATABASE.md")
        return False

    return True

if __name__ == "__main__":
    success = setup_database()
    exit(0 if success else 1)
