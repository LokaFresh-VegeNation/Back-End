import pandas as pd
import numpy as np
import os
import yaml
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.seasonal import STL
import joblib

# ========== KONFIGURASI ==========
def load_config():
        with open(os.path.join("config.yaml"), "r") as f:
            return yaml.safe_load(f)

config = load_config()
MERGED_PATH = config['data_paths']['merged']
SCALER_DIR = config['preprocess_dir']['scaler']
SEQUENCE_DIR = config['preprocess_dir']['sequence']
WINDOW_SIZE = 120

os.makedirs(SCALER_DIR, exist_ok=True)
os.makedirs(SEQUENCE_DIR, exist_ok=True)

# ========== BACA DAN PERSIAPAN DATA ==========
df = pd.read_csv(MERGED_PATH)

df = df.rename(columns={
    'Date': 'date',
    'Inflasi YoY': 'inflasi_yoy',
    'Temp Avg': 'temp',
    'Humidity Avg': 'humidity',
    'RR': 'rainfall',
    'Produksi BM': 'produksi_bm',
    'Produksi BP': 'produksi_bp',
    'Produksi CR': 'produksi_cr',
    'Bawang Merah': 'bawang_merah',
    'Bawang Putih': 'bawang_putih',
    'Cabai Rawit': 'cabai_rawit'
})

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# KOMODITAS TARGET
komoditas = {
    'bawang_merah': 'produksi_bm',
    'bawang_putih': 'produksi_bp',
    'cabai_rawit': 'produksi_cr'
}

# FITUR LAINNYA
def common_features(df, produksi_col):
    return ['inflasi_yoy', 'temp', 'humidity', 'rainfall',
            produksi_col, 'is_tahun_baru', 'is_idul_fitri', 'is_natal']

# ========== FUNGSI PREPROCESS ==========
def preprocess_komoditas(nama, kolom_produksi):
    df_local = df.copy()

    # STL Decomposition
    stl = STL(df_local[nama], period=7)
    result = stl.fit()
    df_local['trend'] = result.trend
    df_local['seasonal'] = result.seasonal
    df_local['residual'] = result.resid

    fitur = ['trend', 'seasonal', 'residual'] + common_features(df_local, kolom_produksi)
    target = [nama]
    data_final = df_local[fitur + target].dropna()

    # Scaling
    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_scaled = scaler_x.fit_transform(data_final[fitur])
    y_scaled = scaler_y.fit_transform(data_final[target])

    # Simpan Scaler
    joblib.dump(scaler_x, os.path.join(SCALER_DIR, f"scaler_x_{nama}.pkl"))
    joblib.dump(scaler_y, os.path.join(SCALER_DIR, f"scaler_y_{nama}.pkl"))

    # Sequence
    def create_sequences(X, y, window):
        Xs, ys = [], []
        for i in range(len(X) - window):
            Xs.append(X[i:i+window])
            ys.append(y[i+window])
        return np.array(Xs), np.array(ys)

    X_seq, y_seq = create_sequences(X_scaled, y_scaled, WINDOW_SIZE)

    # Simpan NPY
    np.save(os.path.join(SEQUENCE_DIR, f"X_{nama}.npy"), X_seq)
    np.save(os.path.join(SEQUENCE_DIR, f"y_{nama}.npy"), y_seq)

    print(f"✅ {nama} preprocessing selesai: {X_seq.shape} input, {y_seq.shape} target")

# ========== JALANKAN UNTUK SEMUA KOMODITAS ==========
for target_name, prod_col in komoditas.items():
    preprocess_komoditas(target_name, prod_col)
