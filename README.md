Oke, aku bikinkan README.md final untuk GitHub yang sudah ada: deskripsi project, setup FastAPI, cara install di VPS, setup PostgreSQL persis dengan kondisi database sekarang, dan cara run.


---

# 🎓 KuisNesa – Platform Kuisioner UNESA

KuisNesa adalah aplikasi **kuisioner digital** berbasis **FastAPI + PostgreSQL** dengan integrasi login Google (restricted ke email UNESA).  
Fitur utama:
- Login dengan akun UNESA (`@unesa.ac.id` / `@mhs.unesa.ac.id`)
- Membuat & mengedit kuisioner (deskripsi, tema, gambar header, akses publik/privat)
- Tambah pertanyaan dengan tipe: **isian singkat, paragraf, pilih salah satu, pilih beberapa, rating**
- Upload media pendukung (gambar/video) per pertanyaan
- Wajib isi (required) per pertanyaan
- Mengisi survey publik dengan progress bar & validasi required
- Statistik jawaban lengkap: grafik batang, pie chart, distribusi rating, word cloud, dll.
- Export hasil kuisioner ke **CSV**
- QR Code untuk berbagi survey

---

## 🚀 Instalasi di VPS

### 1️⃣ Install dependensi dasar

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git postgresql postgresql-contrib

### 2️⃣ Clone project

git clone https://github.com/username/kuisnesa.git
cd kuisnesa

#### 3️⃣ Buat virtualenv & install requirements

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


---

🛢 Setup Database PostgreSQL

1. Buat database & user

sudo -u postgres psql

CREATE DATABASE kuisnesa_db;
CREATE USER kuisnesa_user WITH PASSWORD 'kuisnesa_pass';
GRANT ALL PRIVILEGES ON DATABASE kuisnesa_db TO kuisnesa_user;
\q

2. Konfigurasi database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://kuisnesa_user:kuisnesa_pass@localhost:5432/kuisnesa_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



3. Generate tabel

python3

from database import Base, engine
import models
Base.metadata.create_all(bind=engine)

Cek tabel:

sudo -u postgres psql kuisnesa_db
\dt


---

▶️ Menjalankan Server

1. Jalankan dengan Uvicorn

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

2. Jalankan dengan PM2 (Production)

pip install uvicorn[standard] gunicorn
npm install pm2 -g
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name kuisnesa
pm2 startup
pm2 save


---

📊 Statistik & Visualisasi

Statistik jawaban per pertanyaan

Grafik batang, pie chart

Export hasil kuisioner ke CSV



---

📜 Lisensi

MIT License – bebas digunakan & dikembangkan untuk kebutuhan edukasi.


---

👨‍💻 Pengembang

Dibuat oleh Nauval untuk Universitas Negeri Surabaya 
