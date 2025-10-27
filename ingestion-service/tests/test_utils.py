from app.utils import read_csv
import os
import pandas as pd
import uuid
import pytest


def test_read_csv_ok(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("sku,name\nA1,Product Test")

    df = read_csv(str(p))
    assert isinstance(df, pd.DataFrame)
    assert "import_id" in df.columns
    assert isinstance(df.loc[0, "import_id"], uuid.UUID)


def test_read_csv_missing_file():
    with pytest.raises(ValueError):
        read_csv("nonexistent.csv")
