
import pandas as pd
import numpy as np
import re

df = pd.read_csv("zameen_data.csv")

print("Original shape:", df.shape)
print(df.head())

df.drop_duplicates(subset="url", keep="first", inplace=True)
print("After removing duplicates:", df.shape)

df.replace(["N/A", "n/a", "", " "], np.nan, inplace=True)


text_cols = ["title", "location", "property_type", "purpose", "creation_date"]

for col in text_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace("nan", np.nan)
    )

def parse_price(value):
    if pd.isna(value):
        return np.nan

    value = str(value).lower().replace("pkr", "").strip()

    try:
        if "crore" in value:
            number = float(re.sub(r"[^\d.]", "", value))
            return number * 1_00_00_000  # 1 crore = 1,00,00,000

        elif "lakh" in value:
            number = float(re.sub(r"[^\d.]", "", value))
            return number * 1_00_000  # 1 lakh = 1,00,000

        else:
          
            number = re.sub(r"[^\d.]", "", value)
            return float(number) if number else np.nan

    except Exception:
        return np.nan


df["price_pkr"] = df["price"].apply(parse_price)


for col in ["beds", "baths"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )

def parse_area(value):
    if pd.isna(value):
        return np.nan, np.nan

    value = str(value).strip()
    match = re.search(r"([\d.]+)\s*(Marla|Kanal|Sq\.?\s*Ft\.?|Sq\.?\s*Yd\.?)", value, re.IGNORECASE)

    if match:
        number = float(match.group(1))
        unit = match.group(2).strip().title()
        return number, unit

    return np.nan, np.nan


df[["area_value", "area_unit"]] = df["area"].apply(
    lambda x: pd.Series(parse_area(x))
)


def to_marla(row):
    if pd.isna(row["area_value"]):
        return np.nan

    unit = str(row["area_unit"]).lower()

    if "marla" in unit:
        return row["area_value"]
    elif "kanal" in unit:
        return row["area_value"] * 20
    elif "sq" in unit and "ft" in unit:
        return row["area_value"] / 272.25
    elif "sq" in unit and "yd" in unit:
        return row["area_value"] * 0.037
    else:
        return np.nan


df["area_marla"] = df.apply(to_marla, axis=1)

location_split = df["location"].str.split(",", expand=True)
df["area_name"] = location_split[0].str.strip() if location_split.shape[1] > 0 else np.nan
df["city"] = location_split[location_split.shape[1] - 1].str.strip() if location_split.shape[1] > 1 else np.nan

dha_mask = df["location"].str.contains("DHA", case=False, na=False)
df.loc[dha_mask, "city"] = "DHA, Lahore"

before = df.shape[0]
df.dropna(subset=["price_pkr", "area_marla"], how="all", inplace=True)
after = df.shape[0]
print(f"Dropped {before - after} rows with both price and area missing")


print("\nMissing values per column:")
print(df.isna().sum())

print("\nFinal shape:", df.shape)
print(df.head())


df.to_csv("zameen_data_cleaned.csv", index=False, encoding="utf-8")
print("\nCleaned data saved as zameen_data_cleaned.csv")
