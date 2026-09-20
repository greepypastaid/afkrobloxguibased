# ⚡ Roblox Universal AFK Bot (Background Multitask & Multi-Mode)

Bot otomatisasi cerdas untuk Roblox dan game lainnya berbasis Python. Dilengkapi teknologi **Background Multitasking** yang memungkinkan bot mengirimkan aksi ke jendela game target **tanpa mengganggu mouse atau layar Anda**, sehingga Anda dapat tetap bekerja, mengetik, browsing, atau menonton YouTube!

---

## 🌟 Fitur Utama

### 1. ⚡ Background Multitasking (PostMessage Windows API)
- Mengirimkan klik mouse dan penekanan tombol langsung ke jendela game yang Anda pilih.
- **Bisa Multitasking Penuh**: Kursor mouse Anda tidak akan direbut, dan ketikan Anda di aplikasi lain tidak akan terganggu.
- Dilengkapi **Target Window Selector** (otomatis mendeteksi jendela Roblox, Minecraft, atau aplikasi game lainnya).

---

### 2. 🎮 Berbagai Mode AFK (Multi-Mode)

#### 🎣 Mode 1: Auto Fish ("Fish It" / Fisch / Game Memancing)
Dirancang khusus untuk game memancing di Roblox seperti *Fish It*, *Fisch*, atau *Fishing Simulator*:
- **Fase 1 (Cast)**: Menahan klik kiri untuk melempar joran ke air.
- **Fase 2 (Wait Bite)**: Menunggu jeda waktu realistis sampai umpan disambar ikan.
- **Fase 3 (Reeling In)**: Menarik joran dengan klik beruntun cepat (bisa ditambah tombol Spasi otomatis).
- **Fase 4 (Loop)**: Jeda tangkapan lalu otomatis melempar joran kembali.
- **100% berjalan di background!** Anda bisa memancing seharian sambil nonton video atau browsing.

#### 🚶 Mode 2: Anti-AFK Walk & Jump (3D Classic)
- Pola berjalan aman: **Maju-Mundur (Ping-Pong / Anti-Jurang)**, Pola Kotak, Kiri-Kanan, atau Acak.
- Melompat berkala dengan Spacebar (peluang 0% - 100%).
- Mencegah disconnect 20 menit (*idle kick*) di game 3D.

#### 🖱️ Mode 3: Auto Clicker (Simulator / Clicker Games)
- Klik Kiri atau Klik Kanan otomatis dengan interval kustom (misal: 0.1s - 2.0s).
- Berjalan langsung ke titik tengah jendela game di background.
- Cocok untuk game *Blade Ball*, *Arm Wrestle Simulator*, *Mining Simulator*, dll.

#### ⌨️ Mode 4: Key Spammer / Auto Interact (Farm / Harvest)
- Mengulang penekanan tombol tertentu (misalnya tombol **`E`**, **`F`**, **`Space`**, atau angka **`1`**–**`9`**) dengan jeda waktu kustom.
- Sangat cocok untuk mengumpulkan koin/panen tanaman/membuka telur di simulator game.

---

## 🚀 Cara Menjalankan

### Cara 1: Buka GUI (Paling Mudah)
Cukup **klik dua kali berkas `start.bat`** (atau jalankan `python main.py`).

### Cara 2: Mode Terminal (CLI)
Anda juga bisa menjalankannya lewat Command Prompt atau PowerShell:
```bash
# Menjalankan Auto Fish di background
python cli_afk.py --mode auto_fish

# Menjalankan Auto Clicker di background (klik kiri setiap 0.2 detik)
python cli_afk.py --mode auto_clicker --click-interval 0.2

# Menjalankan Key Spammer (spam tombol 'E' setiap 0.5 detik)
python cli_afk.py --mode key_spammer --key e --key-interval 0.5

# Menjalankan Walk & Jump 3D
python cli_afk.py --mode walk_jump --pattern ping_pong
```

---

## 🎯 Panduan Langkah Demi Langkah (Mode Auto Fish / Fisch)

1. Buka game **Roblox** dan masuk ke permainan memancing (*Fish It* atau *Fisch*).
2. Pegang joran pancing pada karakter Anda dan posisikan di depan air.
3. Buka bot via **`start.bat`**.
4. Pada bagian **"Pilih Game"**, pastikan jendela Roblox Anda terpilih (bot akan otomatis mendeteksinya).
5. Centang **`⚡ Mode Background (Multitasking)`**.
6. Pada dropdown mode, pilih **`🎣 Auto Fish (Fish It / Fisch / Mancing)`**.
7. Klik tombol hijau **`▶ MULAI AFK (F6)`**.
8. Sekarang Anda bisa mengecilkan/membiarkan jendela Roblox di samping dan **bebas membuka browser, Discord, YouTube, atau aplikasi lainnya**. Bot akan terus memancing di background!
9. Untuk berhenti kapan saja, tekan tombol **`F7`** di keyboard atau tombol **`⏹ BERHENTI (F7)`** di bot.

---

## ⌨️ Pintasan Keyboard Global (Hotkeys)

- **`F6`** : Mulai / Lanjutkan bot.
- **`F7`** : Berhenti darurat (*Emergency Stop*). Seketika melepas semua tombol dan menghentikan siklus.

---

## ❓ Tips & Troubleshooting

1. **Jendela Roblox tidak muncul di daftar?**
   - Klik tombol **`🔄 Refresh`** di samping dropdown jendela.
2. **Karakter tidak merespons di background?**
   - Pastikan Roblox tidak diminimalkan ke taskbar dalam kondisi *Minimized* tertutup total (cukup biarkan jendela Roblox terbuka di latar belakang atau di belakang jendela browser Anda).
   - Jika Roblox dijalankan dengan hak akses *Administrator*, jalankan bot ini juga dengan cara klik kanan `start.bat` ➔ **"Run as Administrator"**.
