import requests
import pandas as pd
import yaml
from datetime import datetime

def update_cuaca(): 
    # Load path dari config.yaml
    def load_config():
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)

    API_KEY = '8b438d0e4a9e45c93570892b16363b49'
    
    # Koordinat Bogor, Jabar
    LAT = -6.597147
    LON = 106.806039

    URL = f'https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&units=metric&appid={API_KEY}'
    
    config = load_config()
    FILE_PATH = config['data_paths']['cuaca'] 

    response = requests.get(URL)
    data = response.json()

    data

    today = datetime.now().strftime('%Y-%m-%d')
    temp_avg = data['main']['temp']
    humidity_avg = data['main']['humidity']
    rr = data.get('rain', {}).get('1h', 0.0)  # jika tidak hujan = 0.0

    df = pd.read_csv(FILE_PATH)


    if today in df['Date'].values:
        print(f'Data untuk {today} sudah ada. Tidak ditambahkan ulang.')
    else:
        new_row = {
            'Date': today,
            'Temp Avg': temp_avg,
            'Humidity Avg': humidity_avg,
            'RR': rr
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(FILE_PATH, index=False)
        print(f'Data cuaca untuk {today} berhasil ditambahkan.')


update = update_cuaca()