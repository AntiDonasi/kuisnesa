Oke, aku bikinkan README.md final untuk GitHub yang sudah ada: deskripsi project, setup FastAPI, cara install di VPS, setup PostgreSQL persis dengan kondisi database sekarang, dan cara run.


---

# 🎓 KuisNesa – Platform Kuisioner UNESA

KuisNesa adalah aplikasi **kuisioner digital** berbasis **FastAPI + PostgreSQL** dengan integrasi login Google (restricted ke email UNESA).

## ✨ Fitur Utama

### 🔐 Autentikasi & Profil
- Login dengan akun Google UNESA (`@unesa.ac.id` / `@mhs.unesa.ac.id`)
- Tampilan nama lengkap dan foto profil dari Google
- Role-based access (Mahasiswa/Dosen)

### 📝 Kuisioner
- Membuat & mengedit kuisioner dengan deskripsi lengkap
- Tambah pertanyaan dengan berbagai tipe:
  - Isian singkat
  - Paragraf
  - Pilih salah satu (single choice)
  - Pilih beberapa (multi choice)
  - Rating
- Upload media pendukung (gambar/video) per pertanyaan
- Validasi required per pertanyaan
- Progress bar saat mengisi survey

### 📊 Analisis & Visualisasi (AI-Powered)
- **LDA Topic Modeling** - Ekstrak tema utama dari jawaban
- **Sentiment Analysis** - Analisis sentimen positif/negatif/netral
- **Keyword Extraction** - Top keywords menggunakan TF-IDF
- **Text Statistics** - Rata-rata kata, karakter, dan total respons
- **Bar Chart** - Distribusi jawaban dengan grafik batang
- **Pie Chart** - Persentase distribusi jawaban
- **Word Cloud** - Visualisasi kata populer
- Export hasil ke **CSV**
- QR Code untuk berbagi survey
- JSON API endpoint untuk integrasi

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

## 🛢 Setup Database PostgreSQL

### Quick Setup:

```bash
# 1. Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# 2. Buat database & user
sudo -u postgres psql
CREATE DATABASE kuisioner_db;
CREATE USER kuisioner_user WITH PASSWORD 'passwordku123';
GRANT ALL PRIVILEGES ON DATABASE kuisioner_db TO kuisioner_user;
\q

# 3. Setup environment file
cp .env.example .env
nano .env  # Edit dengan kredensial yang benar

# 4. Setup tables
python3 setup_database.py
```

### 📘 Panduan Lengkap:

Untuk panduan detail setup database, lihat: **[SETUP_DATABASE.md](SETUP_DATABASE.md)**

Panduan lengkap mencakup:
- ✅ Install PostgreSQL di berbagai OS (Ubuntu/Mac/Windows)
- ✅ Konfigurasi user dan permissions
- ✅ Troubleshooting common errors
- ✅ Security best practices
- ✅ Database schema lengkap


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

## 📊 Statistik & Visualisasi

Akses halaman statistik untuk melihat analisis lengkap:
- 📈 **Bar Chart** - Distribusi jawaban
- 🥧 **Pie Chart** - Persentase per kategori
- ☁️ **Word Cloud** - Kata populer
- 🔍 **LDA Topics** - Tema utama (3 topik)
- 🏷️ **Keywords** - Top 10 kata kunci (TF-IDF)
- 🎭 **Sentiment** - Analisis emosi responden
- 📊 **Text Stats** - Statistik text lengkap

### API Endpoint:
```
GET /kuisioner/{id}/stats       # HTML page dengan visualisasi
GET /kuisioner/{id}/analytics   # JSON data untuk integrasi
GET /kuisioner/{id}/export      # Download CSV
```



---

📜 Lisensi

MIT License – bebas digunakan & dikembangkan untuk kebutuhan edukasi.


---

👨‍💻 Pengembang

Dibuat oleh Nauval untuk Universitas Negeri Surabaya 
