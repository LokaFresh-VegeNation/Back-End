import re
import requests, json
from datetime import datetime, timedelta
import pandas as pd
from fuzzywuzzy import process

base_url = 'https://pblpnj.lokatani.id/vegenation'
# base_url = 'http://127.0.0.1:5000/vegenation'
llm_base_url = 'http://localhost:11434' 

def fetch_predictions_from_extracted_info(extracted: dict):
    commodity = extracted.get("PRD")
    num_days = extracted.get("days")

    if commodity is None or num_days is None:
        print("Gagal: Komoditas atau jumlah hari tidak valid.")
        return pd.DataFrame(columns=["date", "price"])

    try:
        url = f"{base_url}/lstm/predict?comodity={commodity}&num_days={num_days}"
        res = requests.get(url)
        data = res.json()["predictions"]
        df = pd.DataFrame(list(data.items()), columns=["date", "price"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df
    except Exception as e:
        print("Gagal mengambil data prediksi:", e)
        return pd.DataFrame(columns=["date", "price"])
    
def fetch_articles():
    try:
        url = f"{base_url}/get_articles"
        url = f"{base_url}/get_articles"
        res = requests.get(url)
        res.raise_for_status()  # Untuk memunculkan error jika status code bukan 200
        data = res.json()["results"]
        df = pd.DataFrame(data, columns=["date", "description", "link", "title"])
        return df
    except Exception as e:
        print("Gagal mengambil data artikel:", e)
        return pd.DataFrame(columns=["date", "description", "link", "title"])

from rapidfuzz import fuzz, process

phrase_corrections = {
    "bawang merah": ["bwang merah", "bawang merahh", "bawwng merah"],
    "bawang putih": ["bawng putih", "bawang puti", "bawang putihh", "bawang puth"],
}

word_corrections = {
    "cabai": ["cabe", "cabeee", "cabee", "cabe rawitt", "cabe rawit", "cabai rawitt", "cabaee", "cabeee"],
    "rawit": ["rawitt", "rawittt", "rawiit"],
    "bawang": ["bwang", "bawang", "bawwng"],
    "harga": ["hrg", "hrga", "hargaa", "hargaaa"],
    "berapa": ["brapa", "brp", "beapa", "beraapa"],
    "untuk": ["utk", "untk", "uuntuk"],
    "kol": ["koll", "kolll", "koli"],
    "hari": ["harii", "hri", "harri", "harii"],
    "minggu": ["mingguu", "mingguuu", "mnggu", "mingo", "mingg"],
    "seminggu": ["semingguu", "semnggu", "seminggo"],
    "setahun": ["setahunn", "setaun", "sethn"],
    "satu": ["sattu", "satoo", "atu"],
    "dua": ["duaa", "duaah"],
    "tiga": ["tigaa", "tigaaa"],
    "empat": ["empaat", "empaat"],
    "lima": ["limaa", "limaa"],
    "enam": ["enaam", "enaam"],
    "tujuh": ["tujuuh", "tujjuh"],
    "delapan": ["delapaan", "dellapan", "delappan"],
    "sembilan": ["sembillan", "semilan", "sembilann"],
    "sepuluh": ["sepuluuh", "sepulh", "sepulu"],
}

def normalize_text(text):
    return re.sub(r'(.)\1{2,}', r'\1', text.lower())

def correct_spelling(user_input):
    user_input = normalize_text(user_input)
    words = user_input.split()
    corrected_words = []
    i = 0
    while i < len(words):
        corrected = False

        # Cek frasa dua kata
        if i < len(words) - 1:
            phrase = f"{words[i]} {words[i+1]}"
            for correct_phrase, variants in phrase_corrections.items():
                if process.extractOne(phrase, variants, score_cutoff=85):
                    corrected_words.append(correct_phrase)
                    i += 2
                    corrected = True
                    break
        if corrected:
            continue

        # Cek kata satuan
        word = words[i]
        best_match = None
        best_score = 0
        for correct_word, variants in word_corrections.items():
            match = process.extractOne(word, variants, score_cutoff=80)
            if match:
                matched_word, score, _ = match
                if score > best_score:
                    best_match = correct_word
                    best_score = score
            else:
                fallback = process.extractOne(word, [correct_word], score_cutoff=90)
                if fallback:
                    best_match = correct_word
        corrected_words.append(best_match if best_match else word)
        i += 1
    return " ".join(corrected_words)

def extract_info(text: str) -> dict:
    result = {"PRD": None, "QTY": None, "days": None}
    text = text.lower()

    # === 1. Produk ===
    if "cabai" in text:
        result["PRD"] = "cabai"
    elif re.search(r"bawang\s*putih", text):
        result["PRD"] = "bawang_putih"
    elif re.search(r"bawang\s*merah", text):
        result["PRD"] = "bawang_merah"

    # === 2. Kuantitas (durasi) ===
    qty_patterns = [
        r"(\d+)\s*(hari|minggu|bulan|tahun)",
        r"(sehari|seminggu|sebulan|setahun)",
        r"(besok)",
        r"(satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh)\s*(hari|minggu|bulan|tahun)"
    ]
    
    durations = []

    for pattern in qty_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            if isinstance(m, tuple):
                qty = " ".join(m)
            else:
                qty = m
            days = convert_to_days(qty)
            if days:
                durations.append((qty, days))

    if durations:
        # Ambil durasi dengan nilai hari terbesar
        max_duration = max(durations, key=lambda x: x[1])
        result["QTY"] = max_duration[0]
        result["days"] = max_duration[1]

    return result

def convert_to_days(duration: str) -> int | None:
    duration = duration.lower()
    mapping = {
        "besok": 1, "hari": 1, "minggu": 7, "bulan": 30, "tahun": 365,
    }
    single_word_mapping = {
        "sehari": 1, "seminggu": 7, "sebulan": 30, "setahun": 365,
    }
    if duration in single_word_mapping:
        return single_word_mapping[duration]

    for satuan in mapping:
        if satuan in duration:
            num = extract_number(duration)
            return num * mapping[satuan]

    return None

def extract_number(text: str) -> int:
    number_map = {
        "satu": 1, "dua": 2, "tiga": 3, "empat": 4,
        "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8,
        "sembilan": 9, "sepuluh": 10
    }
    for word, num in number_map.items():
        if word in text:
            return num
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 1

def chatbot_run(user_input): 
    corrected_input = correct_spelling(user_input)
    print(f"Input setelah spelling correction: {corrected_input}")

    extracted = extract_info(corrected_input)
    print(f"Ekstraksi: {extracted}")

    answer = ""
    df = None
    context = ""

    if "strategi" in corrected_input or "penjualan" in corrected_input or "pembelian" in corrected_input:
        context = build_business_strategy_context(extracted["PRD"])
    elif "berita" in corrected_input or "artikel" in corrected_input:
        df = fetch_articles()
        if df.empty:
            return "Mohon maaf saat ini kami belum memiliki artikel terbaru mengenai bahan pangan"
        else:
            context = build_articles_context(df)
    else:
        df = fetch_predictions_from_extracted_info(extracted)
        print(df.tail())

        if df.empty:
            print("✅ Test: PASS")
            return "Mohon maaf saat ini kami hanya bisa memberikan strategi dan prediksi harga. Komoditas yang kami cakup adalah Cabai, Bawang Merah, dan Bawang Putih"
        else:
            context = build_context(df, extracted["PRD"])

    print(user_input)
    print("🟢 Jawaban untuk pertanyaan pengguna:")
    answer = ask_gemini(user_input, context, extracted["PRD"])
    print(answer)

    return answer

def filter_df_from_today(df):
    today = datetime.today().date()
    df.index = pd.to_datetime(df.index)  # pastikan index datetime
    return df[df.index.date >= today]

def build_context(df, commodity):
    commodity_map = {
        "cabai": "cabai",
        "bawang_merah": "bawang merah",
        "bawang_putih": "bawang putih"
    }
    commodity_name = commodity_map.get(commodity, commodity)  # 
    today = datetime.today().strftime('%d %B %Y')
    context = f"Hari ini adalah {today}.\nBerikut data prediksi harga {commodity_name}:\n"

    filtered_df = filter_df_from_today(df)
    for date, row in filtered_df.iterrows():
        context += f"{date.strftime('%d %B %Y')}: Rp{int(row['price']):,}\n"
    return context

def build_business_strategy_context(commodity):
    """
    Membangun konteks strategi bisnis berdasarkan komoditas yang diekstrak
    menggunakan data dari file JSON knowledge_base_komoditas.json.
    """
    if knowledge_base_data is None:
        load_knowledge_base()
        if knowledge_base_data is None:
             return f"Peringatan: Basis data pengetahuan tidak dapat dimuat. Informasi strategi untuk {commodity} mungkin terbatas."

    commodity_id_lookup = commodity.lower().replace(" ", "_")
    if "cabai" in commodity_id_lookup:
        commodity_id_lookup = "cabai"
    elif "bawang_merah" in commodity_id_lookup or "bamer" in commodity_id_lookup :
        commodity_id_lookup = "bawang_merah"
    elif "bawang_putih" in commodity_id_lookup or "baput" in commodity_id_lookup:
        commodity_id_lookup = "bawang_putih"
    else: # Jika komoditas tidak dikenal setelah normalisasi dasar
        return f"Konteks strategi untuk komoditas '{commodity}' tidak dapat dibangun secara spesifik karena tidak dikenali. Berikan saran umum jika memungkinkan."


    context_parts = [
        f"Anda adalah chatbot ahli strategi jual beli komoditas pertanian. Fokus pada komoditas: {commodity}.",
        "Gunakan informasi detail dari basis pengetahuan berikut untuk menyusun strategi penjualan atau pembelian yang relevan dengan pertanyaan pengguna dan kondisi harga yang mungkin disebutkan:\n"
    ]

    # 1. Informasi Umum Komoditas Spesifik
    commodity_info = next((item for item in knowledge_base_data.get("informasi_umum_komoditas", []) if item.get("id_komoditas") == commodity_id_lookup), None)

    if commodity_info:
        context_parts.append(f"\n--- Informasi Umum untuk {commodity_info.get('nama_komoditas', commodity)} ---")
        if commodity_info.get('jenis_umum'):
            context_parts.append(f"Jenis Umum: {', '.join(commodity_info.get('jenis_umum', []))}")
        context_parts.append(f"Siklus Tanam & Panen: {commodity_info.get('siklus_tanam_panen', 'N/A')}")
        context_parts.append(f"Karakteristik Utama: {commodity_info.get('karakteristik_utama', 'N/A')}")
        context_parts.append(f"Faktor Umum Kenaikan Harga: {'; '.join(commodity_info.get('faktor_pemicu_kenaikan_harga', ['N/A']))}")
        context_parts.append(f"Faktor Umum Penurunan Harga: {'; '.join(commodity_info.get('faktor_pemicu_penurunan_harga', ['N/A']))}")
    else:
        context_parts.append(f"\n[Peringatan: Informasi umum detail untuk komoditas '{commodity}' ({commodity_id_lookup}) tidak ditemukan dalam basis pengetahuan. Berikan jawaban strategi umum jika memungkinkan.]")

    # 2. Analisis Kondisi Harga (Umum, sebagai dasar)
    analisis_harga = knowledge_base_data.get("analisis_kondisi_harga", {})
    if analisis_harga:
        context_parts.append("\n--- Pemahaman Umum Analisis Kondisi Harga ---")
        if analisis_harga.get("tren_harga"):
            context_parts.append("Tren Harga Umum dan Indikasinya:")
            for tren in analisis_harga.get("tren_harga", []):
                context_parts.append(f"  - Jika kondisi harga '{tren.get('kondisi', 'N/A')}', indikasinya adalah '{tren.get('indikasi_umum', 'N/A')}'")
        if analisis_harga.get("indikator_pasar_penting"):
             context_parts.append(f"Indikator Pasar yang Perlu Diperhatikan: {'; '.join(analisis_harga.get('indikator_pasar_penting',[]))}")

    # 3. Kerangka Strategi Penjualan (Umum - chatbot akan diminta menyesuaikan)
    strategi_penjualan = knowledge_base_data.get("strategi_penjualan", {})
    if strategi_penjualan and strategi_penjualan.get('deskripsi'):
        context_parts.append("\n--- Kerangka Umum Strategi Penjualan ---")
        context_parts.append(f"{strategi_penjualan.get('deskripsi')}")
        for kondisi_key, detail_kondisi in strategi_penjualan.items():
            if isinstance(detail_kondisi, dict) and 'nama_kondisi' in detail_kondisi and 'strategi' in detail_kondisi:
                context_parts.append(f"Strategi saat {detail_kondisi.get('nama_kondisi')}:")
                for strategi in detail_kondisi.get('strategi', []):
                    context_parts.append(f"  - Opsi '{strategi.get('nama_strategi', 'N/A')}': {strategi.get('detail', 'N/A')}")

    # 4. Kerangka Strategi Pembelian (Umum)
    strategi_pembelian = knowledge_base_data.get("strategi_pembelian", {})
    if strategi_pembelian and strategi_pembelian.get('deskripsi'):
        context_parts.append("\n--- Kerangka Umum Strategi Pembelian ---")
        context_parts.append(f"{strategi_pembelian.get('deskripsi')}")
        for kondisi_key, detail_kondisi in strategi_pembelian.items():
             if isinstance(detail_kondisi, dict) and 'nama_kondisi' in detail_kondisi and 'strategi' in detail_kondisi:
                context_parts.append(f"Strategi saat {detail_kondisi.get('nama_kondisi')}:")
                for strategi in detail_kondisi.get('strategi', []):
                    context_parts.append(f"  - Opsi '{strategi.get('nama_strategi', 'N/A')}': {strategi.get('detail', 'N/A')}")

    # 5. Faktor Tambahan yang Relevan
    faktor_tambahan = knowledge_base_data.get("faktor_tambahan_pertimbangan", [])
    if faktor_tambahan:
        context_parts.append("\n--- Faktor Tambahan Penting untuk Dipertimbangkan dalam Menyusun Strategi ---")
        context_parts.append("; ".join(faktor_tambahan))

    context_parts.append(f"\nInstruksi untuk AI: Berdasarkan pertanyaan pengguna mengenai '{commodity}', gunakan semua informasi di atas untuk memberikan saran strategi (penjualan atau pembelian) yang paling relevan, spesifik, dan dapat dijalankan. Jika pengguna menyebutkan kondisi harga tertentu (misalnya 'harga sedang naik', 'harga turun'), kaitkan saran dengan kondisi tersebut menggunakan kerangka strategi yang ada.")
    return "\n".join(context_parts)

def build_articles_context(df):
    context = "Berikut adalah artikel-artikel terbaru terkait bahan pangan selama seminggu kebelakang dari detik.com, berikan kesimpulan:\n\n"
    
    for index, row in df.iterrows():
        context += f"{index+1}. {row['title']}\n"
        context += f"Tanggal: {row['date']}\n"
        context += f"Deskripsi: {row['description']}\n"
        context += f"Link: {row['link']}\n\n"
    
    print(context)
    return context

def ask_llama(question, context, commodity):

    today_date = datetime.today().strftime('%d %B %Y')
    
    # Membuat system_prompt dengan hari ini
    system_prompt = (
        f"Jawablah pertanyaan tentang strategi bisnis atau prediksi harga {commodity} hanya berdasarkan konteks yang tersedia. "
        f"Prediksi dimulai dari hari ini ({today_date}) dan hanya boleh dilakukan sampai tanggal terakhir yang tersedia dalam konteks. "
        "Selalu berikan jawaban terakhir dari konteks yang diberikan dan tampilkan harganya"
        "Gunakan **hanya informasi dalam konteks** untuk menjawab. Jangan menambahkan informasi, menyimpulkan, atau memprediksi "
        "selalu gunakan clean teks jangan ada bold dan sebagainya."
        "Untuk pertanyaan sekitar artikel atau berita berikan kesimpulan dari informasi artikel yang diberikan, berikan juga sumber link nya jika perlu"
        # "hal-hal yang tidak disebutkan secara eksplisit dalam data. "
        # "Jika tidak ada data yang tersedia dalam konteks, jawab: 'Saya tidak tahu berdasarkan informasi yang tersedia.' "
    )

    context += (
        f"\nHari ini adalah {today_date}.\n"
        "Jawab pertanyaan user dengan data terakhir yang tersedia."
    )

    response = requests.post(
        f"{llm_base_url}/api/chat",
        json={
            # "model": "llama3.2:1b",
            "model": "llama3.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}"},
                {"role": "user", "content": question}
            ],
            "stream": False
        }
    )

    if response.status_code == 200:
        return response.json()["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyCZObcGVx1_wR4PZDfFUgcgvJmxqmJ_5BQ")

def ask_gemini(question, context, commodity):
    today_date = datetime.today().strftime('%d %B %Y')

    system_prompt = (
        f"Jawablah pertanyaan tentang strategi bisnis atau prediksi harga {commodity} hanya berdasarkan konteks yang tersedia. "
        f"Prediksi dimulai dari hari ini ({today_date}) dan hanya boleh dilakukan sampai tanggal terakhir yang tersedia dalam konteks. "
        "Selalu berikan jawaban terakhir dari konteks yang diberikan dan tampilkan harganya. "
        "Gunakan hanya informasi dalam konteks untuk menjawab. Jangan menambahkan informasi, menyimpulkan, atau memprediksi. "
        "Selalu gunakan teks bersih, jangan ada bold dan sebagainya. "
        "Untuk pertanyaan sekitar artikel atau berita, berikan kesimpulan dari informasi artikel yang diberikan, dan cantumkan sumber link jika perlu."
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"Context:\n{context}\n\n"
        f"Hari ini adalah {today_date}.\n"
        f"Pertanyaan: {question}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                temperature=0.1
            ),
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Error during Gemini API call: {e}"

KNOWLEDGE_BASE_FILE = 'data/strategi.json'
knowledge_base_data = None

def load_knowledge_base(file_path=KNOWLEDGE_BASE_FILE):
    """Memuat basis pengetahuan dari file JSON."""
    global knowledge_base_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge_base_data = json.load(f)
        print(f"Basis pengetahuan '{file_path}' berhasil dimuat.")
    except FileNotFoundError:
        print(f"KESALAHAN: File basis pengetahuan '{file_path}' tidak ditemukan.")
        knowledge_base_data = None # Pastikan None jika gagal
    except json.JSONDecodeError:
        print(f"KESALAHAN: Gagal mendekode JSON dari file '{file_path}'. Pastikan format JSON valid.")
        knowledge_base_data = None # Pastikan None jika gagal
    except Exception as e:
        print(f"KESALAHAN UMUM saat memuat basis pengetahuan: {e}")
        knowledge_base_data = None

def chatbot_run_gemini(user_input, debug=False):
    corrected_input = correct_spelling(user_input)
    explanation = f"📌 Pertanyaan Anda: {user_input}\n"
    explanation += f"📝 Input setelah koreksi ejaan: {corrected_input}\n"

    extracted = extract_info(corrected_input)
    print(extracted)
    explanation += f"🔍 Informasi yang diekstrak: Komoditas: {extracted.get('PRD', 'tidak diketahui')}, Waktu: {extracted.get('QTY', 'tidak diketahui')}\n"

    answer = ""
    df = None
    context = ""

    if "strategi" in corrected_input or "penjualan" in corrected_input or "pembelian" in corrected_input:
        context = build_business_strategy_context(extracted["PRD"])
        explanation += f"📈 Konteks strategi bisnis dibangun berdasarkan data performa produk {extracted['PRD']}.\n"
    elif "berita" in corrected_input or "artikel" in corrected_input:
        df = fetch_articles()
        if df.empty:
            explanation += "⚠️ Tidak ada artikel terbaru yang tersedia. Coba tanyakan komoditas lain atau periksa kembali nanti.\n"
            return explanation if debug else "Mohon maaf saat ini kami belum memiliki artikel terbaru mengenai bahan pangan."
        else:
            context = build_articles_context(df)
            explanation += f"📰 Mengambil {len(df)} artikel terbaru dari detik.com untuk konteks.\n"
    else:
        df = fetch_predictions_from_extracted_info(extracted)
        print(df.tail())
        if df.empty:
            explanation += "⚠️  Data prediksi tidak tersedia. Komoditas yang didukung: Cabai, Bawang Merah, Bawang Putih.\n"
            return explanation if debug else "Mohon maaf saat ini kami hanya bisa memberikan strategi dan prediksi harga. Komoditas yang kami cakup adalah Cabai, Bawang Merah, dan Bawang Putih."
        else:
            context = build_context(df, extracted["PRD"])
            explanation += f"📈 Menggunakan data prediksi harga untuk {extracted['PRD']}.\n"

    # Tambahkan cuplikan konteks dan ringkasan
    explanation += f"\n📊 Cuplikan data:\n{context[:300]}{'...' if len(context) > 300 else ''}\n"

    # Panggil Gemini dengan indikator kepercayaan
    answer = ask_gemini(user_input, context, extracted["PRD"]) 

    if debug:
        return explanation + "\n📢 Jawaban akhir:\n" + answer
    else:
        return answer

def chatbot_run_llama(user_input): 
    corrected_input = correct_spelling(user_input)
    print(f"Input setelah spelling correction: {corrected_input}")

    extracted = extract_info(corrected_input)
    print(f"Ekstraksi: {extracted}")

    answer = ""
    df = None
    context = ""

    if "strategi" in corrected_input or "penjualan" in corrected_input or "pembelian" in corrected_input:
        context = build_business_strategy_context(extracted["PRD"])
    elif "berita" in corrected_input or "artikel" in corrected_input:
        df = fetch_articles()
        if df.empty:
            return "Mohon maaf saat ini kami belum memiliki artikel terbaru mengenai bahan pangan"
        else:
            context = build_articles_context(df)
    else:
        df = fetch_predictions_from_extracted_info(extracted)
        print(df.tail())

        if df.empty:
            print("✅ Test: PASS")
            return "Mohon maaf saat ini kami hanya bisa memberikan strategi dan prediksi harga. Komoditas yang kami cakup adalah Cabai, Bawang Merah, dan Bawang Putih"
        else:
            context = build_context(df, extracted["PRD"])

    print(user_input)
    print("🟢 Jawaban untuk pertanyaan pengguna:")
    # answer = ask_llama(user_input, context, extracted["PRD"])
    answer = ask_gemini(user_input, context, extracted["PRD"])
    print(answer)

    return answer