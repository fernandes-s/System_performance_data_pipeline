import glob
import pandas as pd

files = glob.glob("daily_metrics/*.csv")

df = pd.concat(
    [pd.read_csv(f) for f in files],
    ignore_index=True
)

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

print(df.shape)
print(df.head())
