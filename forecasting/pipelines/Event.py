import pandas as pd
from datetime import datetime, timedelta
from hijri_converter import convert
import yaml

def update_event(): 
    def load_config():
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    
    config = load_config()
    FILE_PATH = config['data_paths']['event'] 

    df = pd.read_csv(FILE_PATH, parse_dates=["Date"])

    last_year = df["Date"].dt.year.max()

    next_year = last_year + 1

    start_date = datetime(next_year, 1, 1)
    end_date = datetime(next_year, 12, 31)
    new_dates = pd.date_range(start=start_date, end=end_date, freq="D")

    def estimate_eid(year):
        try:
            g_date = convert.Hijri(year - 579, 10, 1).to_gregorian()
            return g_date.strftime("%Y-%m-%d")
        except:
            return None

    eid_date = estimate_eid(next_year)
    eid_set = set([eid_date]) if eid_date else set()

    new_df = pd.DataFrame({
        "Date": new_dates.strftime("%Y-%m-%d")
    })
    new_df["is_tahun_baru"] = new_df["Date"].apply(lambda x: 1 if x.endswith("01-01") else 0)
    new_df["is_natal"] = new_df["Date"].apply(lambda x: 1 if x.endswith("12-25") else 0)
    new_df["is_idul_fitri"] = new_df["Date"].apply(lambda x: 1 if x in eid_set else 0)

    combined_df = pd.concat([df, new_df], ignore_index=True)
    combined_df["Date"] = pd.to_datetime(combined_df["Date"]).dt.strftime("%Y-%m-%d")


    combined_df.to_csv(FILE_PATH, index=False)
    print(f"event.csv diperbarui untuk tahun {next_year}.")

update = update_event()