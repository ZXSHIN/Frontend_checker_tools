# Frontend Code Quality Checker

Aplikasi desktop untuk menganalisis kualitas kode frontend sebelum deploy ke produksi. Cukup arahkan ke folder project, klik satu tombol, dan kamu langsung tahu bagian mana yang bermasalah — lengkap dengan skor, detail issue, dan saran perbaikannya.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Tampilan

Antarmuka dark mode dengan sidebar statistik, tab File Analysis, tab Semua Issue, dan panel ekspor laporan — semuanya dalam satu jendela tanpa perlu buka browser atau terminal.

---

## Fitur Utama

- **Auto-detect framework** — Secara otomatis mendeteksi React, Vue, Angular, TypeScript, Tailwind CSS, dan Svelte dari struktur project
- **Scan multi-file** — Mendukung ekstensi `.html`, `.css`, `.scss`, `.sass`, `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, dan `.svelte`
- **100+ aturan kualitas** — Aturan dibagi per kategori: HTML, CSS, JavaScript, React, Vue, Angular, TypeScript, Tailwind, dan universal
- **Skor & grade** — Setiap file dapat skor 0–100. Keseluruhan project juga mendapat skor akhir beserta grade (A–F)
- **Pre-Deploy Checklist** — Daftar pengecekan terakhir sebelum deploy, menunjukkan mana yang lulus dan mana yang gagal
- **Filter issue** — Tampilan issue bisa difilter per kategori: Error, Warning, atau Info
- **Export laporan** — Hasil analisis bisa disimpan ke format **PDF**, **JSON**, atau **TXT**

---

## Struktur Project

```
frontend tools/
├── gui.py                  # Entry point — jalankan file ini
├── requirements.txt        # Daftar dependensi
└── analyzer/
    ├── checker.py          # Logika utama scan dan kalkulasi skor
    ├── detector.py         # Deteksi framework dari struktur folder/file
    └── rules/
        ├── html_rules.py
        ├── css_rules.py
        ├── js_rules.py
        ├── react_rules.py
        ├── vue_rules.py
        ├── angular_rules.py
        ├── typescript_rules.py
        ├── tailwind_rules.py
        └── universal.py
```

---

## Cara Pakai

### 1. Clone atau download project ini

```bash
git clone https://github.com/username/frontend-tools.git
cd frontend-tools
```

### 2. Buat virtual environment (opsional tapi disarankan)

```bash
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # macOS/Linux
```

### 3. Install dependensi

```bash
pip install -r requirements.txt
```

> **Catatan:** Untuk fitur export PDF, pastikan `fpdf2` sudah terinstall. Sudah termasuk di `requirements.txt`, tapi kalau ingin manual:
> ```bash
> pip install fpdf2
> ```

### 4. Jalankan aplikasi

```bash
python gui.py
```

---

## Cara Menggunakan Aplikasi

1. Klik tombol **Browse Folder** untuk memilih folder project frontend kamu
2. Atau langsung ketik path-nya di kolom input, lalu tekan **Enter**
3. Klik **Analisis Sekarang**
4. Tunggu proses scan selesai — hasilnya langsung muncul
5. Lihat tab **File Analysis** untuk ringkasan per file, atau **Semua Issue** untuk daftar lengkap masalah
6. Kalau mau simpan laporannya, klik **Download Laporan PDF**, **JSON**, atau **TXT** di sidebar kanan

---

## Cara Kerja Sistem Skor

Setiap file diperiksa menggunakan aturan yang relevan dengan tipenya. Setiap issue yang ditemukan mengurangi skor:

| Severity | Pengurangan Skor |
|----------|-----------------|
| Error    | Besar           |
| Warning  | Sedang          |
| Info     | Kecil           |

Skor akhir dihitung dari rata-rata semua file, lalu dikonversi ke grade:

| Skor  | Grade | Status         |
|-------|-------|----------------|
| 90–100 | A+   | Siap Deploy    |
| 80–89  | A    | Siap Deploy    |
| 70–79  | B    | Hampir Siap    |
| 60–69  | C    | Butuh Perbaikan|
| < 60   | D/F  | Belum Siap     |

---

## Contoh Aturan yang Dicek

**HTML**
- Tidak ada atribut `alt` pada tag `<img>`
- Tidak ada `<title>` di dalam `<head>`
- Penggunaan tag `<table>` untuk layout (bukan data)
- Formulir tanpa atribut `action`

**CSS / SCSS**
- Penggunaan `!important` berlebihan
- Selector terlalu spesifik (specificity tinggi)
- Properti yang sudah deprecated
- Warna hardcoded tanpa variabel CSS

**JavaScript / TypeScript**
- Penggunaan `var` (lebih baik pakai `const`/`let`)
- `console.log` tertinggal di kode produksi
- Magic number tanpa konstanta bermakna
- Fungsi terlalu panjang

**React**
- Komponen class yang bisa dikonversi ke functional
- `key` prop hilang di dalam `.map()`
- `useEffect` tanpa dependency array
- Import yang tidak digunakan

**Vue**
- Komponen tanpa `name`
- `v-for` dan `v-if` pada elemen yang sama
- Data tidak berupa function

---

## Dependensi

| Package        | Kegunaan                        |
|----------------|---------------------------------|
| `customtkinter >= 5.2.0` | Komponen GUI modern berbasis Tkinter |
| `fpdf2 >= 2.8.0`         | Generate file PDF dari kode Python   |

> `tkinter` sudah bawaan Python, tidak perlu diinstall terpisah.

---

## Requirement Sistem

- Python **3.10** ke atas
- Windows / macOS / Linux
- Resolusi layar minimal **1100 × 720**

---

## Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.
