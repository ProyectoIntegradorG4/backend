import pandas as pd
import uuid

def read_csv(file_path: str) -> pd.DataFrame:
  
    try:
        df = pd.read_csv(file_path, sep=',', encoding='utf-8')
    except Exception as e:
        raise ValueError(f"Error al leer el CSV: {str(e)}")

    df["import_id"] = [uuid.uuid4() for _ in range(len(df))]

    return df

