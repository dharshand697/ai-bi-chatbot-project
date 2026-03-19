import pandas as pd
import os

def load_dataset():
    base_dir = os.getcwd()   # 👈 THIS FIXES EVERYTHING
    file_path = os.path.join(base_dir, "data", "master_dataset.csv")
    
    df = pd.read_csv(file_path)

    # ensure date format
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df