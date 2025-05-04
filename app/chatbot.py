import re
import requests
from datetime import datetime, timedelta
import pandas as pd
from fuzzywuzzy import process
import re

base_url = 'https://pblpnj.lokatani.id/vegenation'
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
    "artikel": ["aritkle", "aritkell", "artikl"],
    "berita": ["berta", "beritaa", "berit"]

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
    # answer = ask_llama(user_input, context, extracted["PRD"])
    answer = ask_gemini(user_input, context, extracted["PRD"])
    print(answer)

    # Validasi jawaban jika data tersedia
    # if df is not None and not df.empty:
    #     last_price = df["price"].iloc[-1]
    #     price_as_int = int(round(last_price))
    #     price_pattern = rf"Rp[\s]*{re.escape(format(price_as_int, ',')).replace(',', '[.,]')}"
    #     if re.search(price_pattern, answer):
    #         print("✅ Harga ditemukan dalam jawaban.")
    #     elif "tidak tahu" in answer.lower():
    #         print("⚠️ Jawaban tidak sesuai: chatbot tidak tahu padahal data tersedia.")
    #     else:
    #         print("❌ Harga tidak disebutkan dalam jawaban.")
    #     print("-" * 60)

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
    context = f"Untuk pertanyaan mengenai strategi penjualan atau pembelian komoditas {commodity}"

    return context

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
                max_output_tokens=500,
                temperature=0.1
            ),
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Error during Gemini API call: {e}"

# MAIN

# print("-----------------------------------------------")

# input = "bagaimana harga bawng putih untuk sebulan kedepan"

# chatbot_run(input)

# Contoh kalimat user yang typo + expected hasil setelah spelling correction
batch_typo_tests = [
    {"input": "harga cabeee 2 hari kedepan berapa", "expected_prd": "cabai", "expected_days": 2},
    {"input": "Bagaimana harga cabe sebulan kedepan?", "expected_prd": "cabai", "expected_days": 30},
    {"input": "bawng merahh brapa hrga nya seminggu kedepan", "expected_prd": "bawang_merah", "expected_days": 7},
    {"input": "harga bawng putihh 3 bulan lagi", "expected_prd": "bawang_putih", "expected_days": 90},
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
            print(f"Input: {test_case['input']}")
            print(f"corrected input: {corrected}")
            print(f"Expected PRD: {test_case['expected_prd']}, Got: {extracted.get('PRD', '')}")
            print(f"Expected Days: {test_case['expected_days']}, Got: {extracted.get('days', '')}")
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

test_questions = [
    "Bagaimana harga cabai seminggu ke depan?",
    "Bagaimana harga cabe sebulan kedepan?",
    "Berapa harga cabai 5 hari ke depan?",
    "Harga cabai sebulan kedepannya?",
    "Prediksi harga cabe dalam 12 hari ke depan?",
    "Bagaimana harga bawang merah seminggu ke depan?",
    "Bagaimana harga bawng merah sebulan kedepan?",
    "Berapa harga bawang putih 5 hari ke depan?",
    "Harga bwang putih sebulan kedepannya?",
]

test_questions_wrong = [
    "Bagaimana harga kol seminggu ke depan?",
    "Bagaimana harga sayur kol sebulan kedepan?",
    "Berapa harga bawang bombai 5 hari ke depan?",
    "Harga timun kedepannya?",
    "Prediksi harga tomat dalam 12 hari ke depan?",
]


def batch_test_chatbot(questions):
    for idx, question in enumerate(questions, 1):
        print(f"\n🧪 Test #{idx}")
        print("=" * 50)
        try:
            chatbot_run(question)
        except Exception as e:
            print(f"❌ Error saat menjalankan chatbot: {e}")
        print("=" * 50)

# batch_test_chatbot(test_questions_wrong)
# batch_test_chatbot(test_questions)

# test_batch_extraction()

# build_articles_context(fetch_articles())