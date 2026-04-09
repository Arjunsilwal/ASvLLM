import pandas as pd
df = pd.read_csv("master_results.csv")

print(f"Total Rows Found: {len(df)}")
print("\nRows per Provider and Mode:")
print(df.groupby(['LLM Provider', 'Mode']).size())