# SiHijau Backend API

Backend service untuk platform **SiHijau** (Smart Waste Scanner & Waste Management Platform) berbasis **Python 3.11+**, **FastAPI**, **PostgreSQL + PostGIS**, **MinIO (AWS S3)**, dan **SQLAdmin**.

---

## 🚀 Tech Stack

* **Framework:** FastAPI (Python 3.11+)
* **Database & Geo:** PostgreSQL 16 + PostGIS
* **ORM & Migration:** SQLAlchemy 2.0 (Async) + asyncpg + Alembic
* **Object Storage:** MinIO (Local S3-compatible) / AWS S3
* **Cache:** Redis 7
* **Admin Dashboard:** SQLAdmin
* **AI Vision:** Google Gemini 1.5 Flash Vision / Intelligent Fallback Mock

---

## 🐳 Quick Start dengan Docker

### 1. Jalankan Service Pendukung (PostgreSQL, MinIO, Redis)

```bash
docker compose up -d
```

Service yang akan aktif:
* **PostgreSQL (PostGIS):** `localhost:5433`
* **MinIO S3 API:** `http://localhost:9000`
* **MinIO Web Console:** `http://localhost:9001` (User: `sihijau_minio`, Password: `sihijau_minio123`)
* **Redis:** `localhost:6379`

---

## 🔌 Cara Konek DBeaver ke Database Docker

> **Penjelasan Docker vs DBeaver:**
> * **PostgreSQL di Docker** adalah mesin database-nya (*server engine*) yang berjalan di background.
> * **DBeaver** adalah aplikasi GUI desktop untuk melihat, mengedit tabel, dan menjalankan query SQL secara visual.

### Langkah Koneksi di DBeaver:
1. Buka DBeaver.
2. Klik tombol **New Database Connection** (icon colokan listrik bertanda plus) ➡️ pilih **PostgreSQL**.
3. Masukkan parameter koneksi:
   * **Host:** `localhost`
   * **Port:** `5433`
   * **Database:** `sihijau_db`
   * **Username:** `sihijau_user`
   * **Password:** `sihijau_password`
4. Klik **Test Connection** (pastikan sudah berhasil / centang hijau).
5. Klik **Finish**.

---

## 💻 Menjalankan Backend FastAPI di Lokal

### 1. Buat Virtual Environment & Install Dependensi

```bash
python -m venv .venv
# Di Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Jalankan Seeding Data Awal

```bash
python scripts/seed.py
```

Data default yang dibuat:
* **Admin User:** `admin@sihijau.id` / `admin123`
* **Demo User:** `raka@sihijau.id` / `password123`
* **Contoh Data Mitra:** Bank Sampah Malang Pusat, Rumah Maggot BSF Lestari, TPS 3R Hijau Berseri
* **Contoh Panduan:** Pembuatan Kompos Takakura, Pembuatan Ecobrick

### 3. Jalankan Server FastAPI & Pantau Log di Terminal

Jalankan perintah berikut di terminal (PowerShell atau terminal VS Code):

```powershell
# Jalankan uvicorn dengan auto-reload dan level logging INFO
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level info
```

Setiap request dari Postman / Frontend akan langsung terpantau secara real-time di terminal dengan format:
```text
2026-10-07 17:32:10,275 [INFO] sihijau.api: [GET] /health -> 200 (61.69ms) from 127.0.0.1
```

---

## 🔐 Google Authentication (OAuth 2.0)

Backend telah mendukung integrasi Google Authentication sesuai **best practice industri**:
1. **Mobile & SPA (ID Token Flow - Recommended):** Frontend/Mobile login via Google Sign-In SDK, lalu mengirim `id_token` ke endpoint `POST /api/v1/auth/google`. Backend memverifikasi tanda tangan kriptografi token langsung ke server Google.
2. **Web Browser Consent Flow (OAuth Code Flow):**
   * Endpoint `GET /api/v1/auth/google/url` menghasilkan link consent Google.
   * Endpoint `GET /api/v1/auth/google/callback` menerima `code` redirect dan menukarnya dengan session token.
3. **Instant Development Mock:** Endpoint `POST /api/v1/auth/google/dev-mock` untuk testing langsung di Postman tanpa perlu kredensial Google Cloud Console terlebih dahulu.

### Konfigurasi `.env`:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

---

## 📮 Testing API Melalui Postman

File konfigurasi Postman telah disediakan di root repository:
* **Collection:** `postman_collection.json`
* **Environment:** `postman_environment.json`

### Langkah-langkah Testing di Postman:
1. Buka aplikasi **Postman**.
2. Klik tombol **Import** (di pojok kiri atas).
3. Drag & drop kedua file:
   * `postman_collection.json`
   * `postman_environment.json`
4. Pilih active environment di pojok kanan atas Postman: **SiHijau Local Environment**.
5. Buka folder **01. Authentication & Google OAuth**:
   * Jalankan request **Google Dev Mock Login (Instant Test)** atau **Google Login (ID Token Flow)**.
   * Token Bearer (`{{token}}`) akan otomatis disimpan ke environment Postman melalui script otomatis!
6. Anda sekarang dapat langsung menjalankan request lain (Decision Engine, Processing Guides, Partner Directory, Action Logs, dll.) tanpa perlu copy-paste token manual!

---

## 📌 Endpoint & Dashboard Penting

* **Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Admin Dashboard (SQLAdmin):** [http://localhost:8000/admin](http://localhost:8000/admin)
* **MinIO Web Console (S3 Storage):** [http://localhost:9001](http://localhost:9001)

