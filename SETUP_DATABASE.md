# 🗄️ Setup Database PostgreSQL - KuisNesa

Panduan lengkap setup database PostgreSQL untuk project KuisNesa.

---

## 📋 Prasyarat

- PostgreSQL 12+ terinstall
- Python 3.8+ terinstall
- Access ke terminal/command line

---

## 🚀 Langkah-Langkah Setup

### 1️⃣ Install PostgreSQL

#### **Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### **macOS (dengan Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

#### **Windows:**
Download installer dari: https://www.postgresql.org/download/windows/

---

### 2️⃣ Start PostgreSQL Service

#### **Ubuntu/Debian:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
sudo systemctl status postgresql  # Check status
```

#### **macOS:**
```bash
brew services start postgresql@14
```

#### **Windows:**
PostgreSQL service akan auto-start setelah install.

---

### 3️⃣ Akses PostgreSQL Shell

```bash
# Login sebagai postgres user (default superuser)
sudo -u postgres psql

# Atau langsung (jika user sudah dikonfigurasi)
psql -U postgres
```

---

### 4️⃣ Buat Database dan User

Jalankan command berikut di PostgreSQL shell:

```sql
-- Buat database
CREATE DATABASE kuisioner_db;

-- Buat user dengan password
CREATE USER kuisioner_user WITH PASSWORD 'passwordku123';

-- Berikan semua privileges ke user
GRANT ALL PRIVILEGES ON DATABASE kuisioner_db TO kuisioner_user;

-- (PostgreSQL 15+) Grant schema privileges
\c kuisioner_db
GRANT ALL ON SCHEMA public TO kuisioner_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kuisioner_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kuisioner_user;

-- Keluar dari psql
\q
```

#### **Verifikasi Database & User:**
```bash
# List databases
sudo -u postgres psql -c "\l"

# List users
sudo -u postgres psql -c "\du"

# Test login dengan user baru
psql -U kuisioner_user -d kuisioner_db -h localhost
# Masukkan password: passwordku123
```

---

### 5️⃣ Konfigurasi File .env

Copy `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
nano .env  # atau gunakan editor lain
```

Isi `.env` dengan konfigurasi yang benar:

```env
DATABASE_URL=postgresql://kuisioner_user:passwordku123@localhost:5432/kuisioner_db

GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

SECRET_KEY=your_secret_key_here
```

#### **Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### 6️⃣ Install Python Dependencies

```bash
# Pastikan sudah di virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### 7️⃣ Setup Database Tables

Jalankan script setup database:

```bash
python3 setup_database.py
```

Output yang diharapkan:
```
🔧 Setting up KuisNesa database...
📦 Creating tables for models: User, Kuisioner, Question, Response
✅ Database setup completed successfully!

📋 Tables created:
   - users
   - kuisioners
   - questions
   - responses

🚀 You can now run the application with: uvicorn main:app --reload
```

---

### 8️⃣ Verifikasi Tables

```bash
# Akses database
psql -U kuisioner_user -d kuisioner_db -h localhost

# List tables
\dt

# Describe table structure
\d users
\d kuisioners
\d questions
\d responses

# Keluar
\q
```

Output yang diharapkan:
```
             List of relations
 Schema |    Name     | Type  |      Owner
--------+-------------+-------+-----------------
 public | kuisioners  | table | kuisioner_user
 public | questions   | table | kuisioner_user
 public | responses   | table | kuisioner_user
 public | users       | table | kuisioner_user
```

---

### 9️⃣ Jalankan Aplikasi

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Buka browser: http://localhost:8000

---

## 🔧 Troubleshooting

### ❌ Error: "FATAL: Peer authentication failed"

**Solusi:** Edit `pg_hba.conf`

```bash
# Find pg_hba.conf
sudo find /etc/postgresql -name pg_hba.conf

# Edit file
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Ubah baris:
```
local   all             all                                     peer
```

Menjadi:
```
local   all             all                                     md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

### ❌ Error: "password authentication failed"

**Solusi:** Reset password user

```sql
sudo -u postgres psql
ALTER USER kuisioner_user WITH PASSWORD 'password_baru';
\q
```

Update `.env` dengan password baru.

---

### ❌ Error: "database does not exist"

**Solusi:** Buat database secara manual

```bash
sudo -u postgres createdb kuisioner_db
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kuisioner_db TO kuisioner_user;"
```

---

### ❌ Error: "connection refused"

**Solusi:** Pastikan PostgreSQL running

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

### ❌ Error: "permission denied for schema public" (PostgreSQL 15+)

**Solusi:**
```sql
sudo -u postgres psql -d kuisioner_db
GRANT ALL ON SCHEMA public TO kuisioner_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kuisioner_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kuisioner_user;
\q
```

---

## 🔐 Security Best Practices

### 1. **Password yang Kuat**
```bash
# Generate strong password
openssl rand -base64 32
```

### 2. **Jangan Commit .env ke Git**
File `.env` sudah ada di `.gitignore`

### 3. **Production Settings**
Untuk production, gunakan:
- Password yang kompleks
- SSL connection
- Separate user dengan privileges terbatas

---

## 📊 Database Schema

### Table: `users`
```sql
- id (INTEGER, PRIMARY KEY)
- nama (VARCHAR(100))
- email (VARCHAR(120), UNIQUE)
- role (VARCHAR(20))
- photo_url (VARCHAR(500))
```

### Table: `kuisioners`
```sql
- id (INTEGER, PRIMARY KEY)
- title (VARCHAR(200))
- description (TEXT)
- background (VARCHAR(200))
- theme (VARCHAR(50))
- start_date (TIMESTAMP)
- end_date (TIMESTAMP)
- access (VARCHAR(20))
- owner_id (INTEGER, FOREIGN KEY -> users.id)
```

### Table: `questions`
```sql
- id (INTEGER, PRIMARY KEY)
- text (TEXT)
- description (TEXT)
- qtype (VARCHAR(50))
- options (TEXT)
- required (BOOLEAN)
- media_url (VARCHAR(255))
- kuisioner_id (INTEGER, FOREIGN KEY -> kuisioners.id)
```

### Table: `responses`
```sql
- id (INTEGER, PRIMARY KEY)
- answer (TEXT)
- user_id (INTEGER, FOREIGN KEY -> users.id)
- question_id (INTEGER, FOREIGN KEY -> questions.id)
- UNIQUE CONSTRAINT (user_id, question_id)
```

---

## 🎯 Quick Start (TL;DR)

```bash
# 1. Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# 2. Buat database dan user
sudo -u postgres psql
CREATE DATABASE kuisioner_db;
CREATE USER kuisioner_user WITH PASSWORD 'passwordku123';
GRANT ALL PRIVILEGES ON DATABASE kuisioner_db TO kuisioner_user;
\q

# 3. Setup environment
cp .env.example .env
nano .env  # Edit dengan kredensial yang benar

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup tables
python3 setup_database.py

# 6. Run application
uvicorn main:app --reload
```

---

## 📞 Butuh Bantuan?

- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

✅ **Database setup selesai!** Sekarang aplikasi siap digunakan! 🚀
