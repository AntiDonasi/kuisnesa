#!/bin/bash
# Quick Database Commands for KuisNesa

echo "🗄️  KuisNesa Database Quick Commands"
echo "===================================="
echo ""

# Check PostgreSQL status
echo "📊 PostgreSQL Status:"
service postgresql status | head -1
echo ""

# Quick commands
echo "💡 Quick Commands:"
echo ""
echo "1️⃣  Start PostgreSQL:"
echo "   service postgresql start"
echo ""
echo "2️⃣  Stop PostgreSQL:"
echo "   service postgresql stop"
echo ""
echo "3️⃣  Restart PostgreSQL:"
echo "   service postgresql restart"
echo ""
echo "4️⃣  Check Status:"
echo "   service postgresql status"
echo ""
echo "5️⃣  Connect to Database:"
echo "   PGPASSWORD='passwordku' psql -U kuisioner_user -h localhost -d kuisioner_db"
echo ""
echo "6️⃣  Setup/Reset Tables:"
echo "   python3 setup_database.py"
echo ""
echo "7️⃣  Run Application:"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🔍 Database Info:"
PGPASSWORD='passwordku' psql -U kuisioner_user -h localhost -d kuisioner_db -c "
SELECT
    'Database: ' || current_database() as info
UNION ALL
SELECT
    'User: ' || current_user
UNION ALL
SELECT
    'Tables: ' || count(*)::text
FROM information_schema.tables
WHERE table_schema = 'public';
" -t 2>/dev/null || echo "⚠️  PostgreSQL not running or connection failed"
