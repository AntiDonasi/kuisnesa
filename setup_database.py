#!/usr/bin/env python3
"""
Setup Database Script for KuisNesa
This script will create all necessary tables in PostgreSQL database
"""

from database import Base, engine
import models

def setup_database():
    """Create all tables in the database"""
    print("🔧 Setting up KuisNesa database...")
    print(f"📦 Creating tables for models: User, Kuisioner, Question, Response")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database setup completed successfully!")
        print("\n📋 Tables created:")
        print("   - users")
        print("   - kuisioners")
        print("   - questions")
        print("   - responses")
        print("\n🚀 You can now run the application with: uvicorn main:app --reload")

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\n💡 Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. Database exists (create it with: createdb kuisioner_db)")
        print("   3. .env file has correct DATABASE_URL")
        print("   4. User has necessary permissions")
        return False

    return True

if __name__ == "__main__":
    setup_database()
