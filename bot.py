!pip install python-telegram-bot==20.3 requests nest_asyncio
import asyncio
import requests
import re  # Untuk validasi input
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Terapkan nest_asyncio agar async berjalan di Google Colab
nest_asyncio.apply()

# Konfigurasi API
TELEGRAM_TOKEN = "8177044371:AAGT7-kDL4xbv1tfrOVgLoyhcPrhVCoqwy4"
GEMINI_API_KEY = "AIzaSyALLWcXxIvquP_VfX4DzboHGIXu2VHEQKY"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Dictionary untuk menyimpan data pengguna
chat_history = {}  # {user_id: [(pertanyaan, jawaban)]}
user_schedules = {}  # {user_id: {hari: [jadwal]}}

# Fungsi untuk mengakses AI Gemini
def query_gemini_api(question):
    try:
        response = requests.post(GEMINI_API_URL, json={"contents": [{"parts": [{"text": question}]}]}, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Maaf, tidak ada jawaban.")
    except Exception as e:
        return f"Terjadi kesalahan: {e}"

# Fungsi untuk menangani perintah /start
async def mulai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Halo! Saya AI Chatbot berbasis Gemini. Gunakan /help untuk melihat fitur!")

# Fungsi untuk menampilkan bantuan
async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 **Fitur yang tersedia:**\n"
        "🔹 /riwayat - Melihat riwayat percakapan\n"
        "🔹 /kalkulator <ekspresi> - Kalkulator\n"
        "🔹 /konversi <C/F/K/R> <angka> - Konversi suhu dari °C ke °F, K, dan Ré\n"
        "🔹 /setjadwal <hari> <jam> <kegiatan> - Menyimpan jadwal harian\n"
        "🔹 /jadwal <hari> - Melihat jadwal harian\n"
        "🔹 /hapusjadwal <hari> <jam> - Menghapus jadwal harian\n"
    )
    await update.message.reply_text(help_text)

# Fungsi untuk menangani command yang tidak dikenal
async def command_salah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Perintah tidak dikenal! Gunakan /help untuk melihat daftar perintah yang tersedia."
    )

# Fungsi untuk menangani pesan pengguna & menyimpan riwayat
async def menangani_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_message = update.message.text.strip()

    if not user_message:
        await update.message.reply_text("⚠️ Pesan kosong! Silakan masukkan pertanyaan yang valid.")
        return

    bot_response = query_gemini_api(user_message)

    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append((user_message, bot_response))

    await update.message.reply_text(bot_response)

# Fungsi untuk menampilkan riwayat percakapan
async def riwayat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    history = chat_history.get(user_id, [])

    if history:
        history_text = "\n\n".join([f"👤 {q}\n🤖 {a}" for q, a in history[-10:]])  # Ambil 5 percakapan terakhir
        await update.message.reply_text(f"📜 Riwayat Percakapan:\n\n{history_text}")
    else:
        await update.message.reply_text("📭 Riwayat kosong. Mulai bertanya!")

# Fungsi Kalkulator dengan validasi input
async def kalkulator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args).strip()

    if not user_input:
        await update.message.reply_text("⚠️ Gunakan format: /kalkulator <ekspresi>. Contoh: /kalkulator 5+3*2")
        return

    if not re.match(r"^[0-9+\-*/(). ]+$", user_input):
        await update.message.reply_text("⚠️ Ekspresi tidak valid! Gunakan hanya angka dan operator + - * / ()")
        return

    try:
        result = eval(user_input)
        await update.message.reply_text(f"🧮 Hasil: {result}")
    except Exception:
        await update.message.reply_text("⚠️ Terjadi kesalahan dalam perhitungan!")

# Fungsi Konversi Suhu dari berbagai satuan
def konversi_suhu(unit, value):
    unit = unit.upper()
    value = float(value)

    if unit == "C":
        fahrenheit = (value * 9/5) + 32
        kelvin = value + 273.15
        reamur = value * 4/5
        result = (
            f"🔥 **Konversi Suhu dari {value}°C** 🔥\n"
            f"🌡 {fahrenheit:.2f}°F\n"
            f"🌡 {kelvin:.2f}K\n"
            f"🌡 {reamur:.2f}°Ré"
        )

    elif unit == "F":
        celsius = (value - 32) * 5/9
        kelvin = (value - 32) * 5/9 + 273.15
        reamur = (value - 32) * 4/9
        result = (
            f"🔥 **Konversi Suhu dari {value}°F** 🔥\n"
            f"🌡 {celsius:.2f}°C\n"
            f"🌡 {kelvin:.2f}K\n"
            f"🌡 {reamur:.2f}°Ré"
        )

    elif unit == "K":
        celsius = value - 273.15
        fahrenheit = (value - 273.15) * 9/5 + 32
        reamur = (value - 273.15) * 4/5
        result = (
            f"🔥 **Konversi Suhu dari {value}K** 🔥\n"
            f"🌡 {celsius:.2f}°C\n"
            f"🌡 {fahrenheit:.2f}°F\n"
            f"🌡 {reamur:.2f}°Ré"
        )

    elif unit == "R":
        celsius = value * 5/4
        fahrenheit = (value * 9/4) + 32
        kelvin = (value * 5/4) + 273.15
        result = (
            f"🔥 **Konversi Suhu dari {value}°Ré** 🔥\n"
            f"🌡 {celsius:.2f}°C\n"
            f"🌡 {fahrenheit:.2f}°F\n"
            f"🌡 {kelvin:.2f}K"
        )

    else:
        return "⚠️ Format tidak valid! Gunakan format: /konversi <C/F/K/R> <angka>"

    return result

# Fungsi Telegram untuk Konversi Suhu
async def konversi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            raise ValueError("Kurang argumen")

        unit = context.args[0].upper()
        value = float(context.args[1])

        if unit not in ["C", "F", "K", "R"]:
            raise ValueError("Satuan tidak valid")

        result = konversi_suhu(unit, value)
        await update.message.reply_text(result)

    except ValueError:
        await update.message.reply_text("⚠️ Gunakan format: /konversi <C/F/K/R> <angka>. Contoh: /konversi C 100")

# Fungsi untuk menyimpan jadwal dengan validasi input
async def tambah_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    args = context.args

    if len(args) < 3:
        await update.message.reply_text("⚠️ Gunakan format: /setjadwal <hari> <jam> <kegiatan>. Contoh : /setjadwal Senin 08:00 Ngampus")
        return

    hari = args[0].capitalize()
    jam = args[1]
    kegiatan = " ".join(args[2:])

    if not re.match(r"^\d{2}:\d{2}$", jam):  # Validasi format jam (hh:mm)
        await update.message.reply_text("⚠️ Format jam tidak valid! Gunakan format HH:MM. Contoh: 08:30")
        return

    if user_id not in user_schedules:
        user_schedules[user_id] = {}

    if hari not in user_schedules[user_id]:
        user_schedules[user_id][hari] = []

    user_schedules[user_id][hari].append(f"{jam} - {kegiatan}")
    await update.message.reply_text(f"✅ Jadwal ditambahkan: {hari} {jam} - {kegiatan}")

# Fungsi untuk melihat jadwal dengan validasi
async def lihat_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    args = context.args

    if not args:
        await update.message.reply_text("⚠️ Gunakan format: /jadwal <hari>. Contoh: /jadwal Senin")
        return

    hari = args[0].capitalize()
    schedule = user_schedules.get(user_id, {}).get(hari, [])

    if schedule:
        schedule_text = "\n".join(schedule)
        await update.message.reply_text(f"📅 Jadwal {hari}:\n{schedule_text}")
    else:
        await update.message.reply_text(f"📭 Tidak ada jadwal untuk {hari}.")

# Fungsi untuk menghapus jadwal
async def hapus_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text("⚠️ Gunakan format: /hapusjadwal <hari> <jam>. Contoh: /hapusjadwal Senin 08:00")
        return

    hari = args[0].capitalize()
    jam = args[1]

    if user_id not in user_schedules or hari not in user_schedules[user_id]:
        await update.message.reply_text(f"📭 Tidak ada jadwal untuk {hari}.")
        return

    # Cari dan hapus jadwal yang sesuai
    jadwal_hari_ini = user_schedules[user_id][hari]
    jadwal_ditemukan = [j for j in jadwal_hari_ini if j.startswith(jam)]

    if not jadwal_ditemukan:
        await update.message.reply_text(f"⚠️ Tidak ada jadwal di {hari} pada {jam}.")
        return

    # Hapus semua jadwal yang memiliki jam yang sesuai
    for j in jadwal_ditemukan:
        jadwal_hari_ini.remove(j)

    # Hapus hari dari dictionary jika kosong
    if not jadwal_hari_ini:
        del user_schedules[user_id][hari]

    await update.message.reply_text(f"✅ Jadwal di {hari} pada {jam} telah dihapus.")

# Fungsi utama untuk menjalankan bot
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", mulai))
    app.add_handler(CommandHandler("help", bantuan))
    app.add_handler(CommandHandler("riwayat", riwayat))
    app.add_handler(CommandHandler("kalkulator", kalkulator))
    app.add_handler(CommandHandler("konversi", konversi))
    app.add_handler(CommandHandler("setjadwal", tambah_jadwal))
    app.add_handler(CommandHandler("jadwal", lihat_jadwal))
    app.add_handler(CommandHandler("hapusjadwal", hapus_jadwal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menangani_pesan))
    app.add_handler(MessageHandler(filters.COMMAND, command_salah))
    print("🤖 Bot berjalan...")
    await app.run_polling()

# Menjalankan bot di Google Colab
loop = asyncio.get_event_loop()
loop.run_until_complete(main())