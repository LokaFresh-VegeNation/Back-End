import re
import requests
from datetime import datetime, timedelta
import pandas as pd
from fuzzywuzzy import process

base_url = 'http://127.0.0.1:5000'

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

from rapidfuzz import fuzz, process

correction_dict = {
    "cabai": ["cabe", "cabeee", "cabee", "cabe rawitt", "cabe rawit", "cabai rawitt", "cabaee", "cabeee"],
    "rawit": ["rawitt", "rawittt", "rawiit"],
    "bawang merah": ["bwang merah", "bawang merahh", "bawwng merah"],
    "bawang putih": ["bawng putih", "bawang puti", "bawang putihh", "bawang puth"],
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
    import re
    return re.sub(r'(.)\1{2,}', r'\1', text.lower())

def correct_spelling(user_input):
    user_input = normalize_text(user_input)
    words = user_input.split()
    corrected_words = []
    for word in words:
        best_match = None
        best_score = 0
        for correct_word, variants in correction_dict.items():
            matches = process.extractOne(word, variants, score_cutoff=80)
            if matches:
                matched_word, score, _ = matches
                if score > best_score:
                    best_match = correct_word
                    best_score = score
            else:
                score = process.extractOne(word, [correct_word], score_cutoff=90)
                if score:
                    best_match = correct_word
        corrected_words.append(best_match if best_match else word)
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
    elif "bawang" in text and "putih" in text:
        result["PRD"] = "bawang_putih"
    elif "bawang" in text and "merah" in text:
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
    
    # Tentukan apakah pertanyaan tentang strategi atau harga
    if "strategi" in user_input or "penjualan" in user_input or "pembelian" in user_input:
        # Menyusun konteks untuk pertanyaan tentang strategi bisnis
        context = build_business_strategy_context(user_input, extracted["PRD"])
    else:
        # Menyusun konteks untuk pertanyaan tentang harga
        df = fetch_predictions_from_extracted_info(extracted)
        print(df)
        if df.empty:
            print("Tidak ada data prediksi tersedia.")
            return
        context = build_context(df, extracted["PRD"])
    
    # Tanyakan ke Llama
    print(user_input)
    print("🟢 Jawaban untuk pertanyaan pengguna:")
    answer = ask_llama(user_input, context, extracted["PRD"])
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


def build_business_strategy_context(user_input, commodity):
    context = f"Untuk pertanyaan mengenai strategi penjualan atau pembelian komoditas {commodity}, berikut beberapa pertimbangan penting:\n"
 
    if "cabai" in commodity:
        context += "Strategi penjualan cabai biasanya melibatkan pemantauan harga pasar secara rutin dan perencanaan stok untuk menghindari kekurangan atau kelebihan pasokan.\n"
    elif "bawang merah" in commodity:
        context += "Untuk bawang merah, penting untuk memperhatikan musim panen dan menjaga rantai pasokan yang efisien agar harga tetap stabil.\n"
    elif "bawang putih" in commodity:
        context += "Bawang putih sering dipengaruhi oleh faktor impor dan kuota impor pemerintah, jadi penting untuk memantau kebijakan terkait impor untuk menentukan strategi pembelian yang tepat.\n"
    
    if "penjualan" in user_input:
        context += "Untuk penjualan, perlu adanya strategi pemasaran yang tepat dan juga analisis kebutuhan pasar secara teratur."
    elif "pembelian" in user_input:
        context += "Untuk pembelian, disarankan untuk membeli dalam jumlah besar ketika harga sedang rendah dan mempertimbangkan penyimpanan yang baik untuk menghindari kerugian karena kerusakan produk."

    return context


def ask_llama(question, context, commodity):
    # Mendapatkan tanggal hari ini
    today_date = datetime.today().strftime('%d %B %Y')
    
    # Membuat system_prompt dengan hari ini
    system_prompt = (
        f"Gunakan konteks untuk menjawab pertanyaan tentang strategi bisnis atau prediksi harga {commodity}. "
        f"Prediksi selalu dimulai dari hari ini ({today_date}) hiraukan kata ke depan. Gunakan **hanya data yang sudah tersedia** untuk "
        "menjawab pertanyaan. Jangan membuat prediksi atau menyimpulkan harga berdasarkan data yang tidak ada. "
        "Jika pertanyaan mengarah pada masa depan, jawab berdasarkan data yang sudah ada, tanpa memprediksi atau "
        "menyimpulkan sesuatu yang tidak ada dalam data. jawab dengan simpel dan tidak bertele tele"
    )

    # Tambahkan tanggal hari ini ke dalam konteks
    context += f"\nHari ini adalah {today_date}.\n"

    response = requests.post(
        "http://localhost:11434/api/chat",
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


# MAIN

# print("-----------------------------------------------")
# input = "bagaimana harga cabai seminggu"
# chatbot_run(input)

# Contoh kalimat user yang typo + expected hasil setelah spelling correction
batch_typo_tests = [
    {"input": "harga cabeee 2 hari kedepan berapa", "expected_prd": "cabai", "expected_days": 2},
    {"input": "bawang merah brapa hrga nya seminggu kedepan", "expected_prd": "bawang_merah", "expected_days": 7},
    {"input": "harga bawang putih 3 bulan lagi", "expected_prd": "bawang_putih", "expected_days": 90},
    {"input": "harga cabe rawitt utk 5 hari", "expected_prd": "cabai", "expected_days": 5},
]

def test_batch_extraction():
    print("🧪 Memulai batch test extract_info...")
    success = 0
    for idx, test_case in enumerate(batch_typo_tests):
        corrected = correct_spelling(test_case["input"])
        extracted = extract_info(corrected)
        prd_match = extracted.get("PRD", "").lower() == test_case["expected_prd"].lower()
        days_match = extracted.get("days", None) == test_case["expected_days"]
        if prd_match and days_match:
            print(f"✅ Test {idx+1}: PASS")
            success += 1
        else:
            print(f"❌ Test {idx+1}: FAIL")
            print(f"Input: {test_case['input']}")
            print(f"corrected input: {corrected}")
            print(f"Expected PRD: {test_case['expected_prd']}, Got: {extracted.get('PRD', '')}")
            print(f"Expected Days: {test_case['expected_days']}, Got: {extracted.get('days', '')}")
            print("---")
    print(f"\n🎯 Hasil Akhir: {success}/{len(batch_typo_tests)} test lulus.")

# test_batch_extraction()