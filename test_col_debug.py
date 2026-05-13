import sys
sys.path.insert(0, '/Users/gavindominique/Documents/TukeyLab')
import pandas as pd
from pathlib import Path

# Load spotify dataset
project = Path('/Users/gavindominique/Documents/TukeyLab/projects/test_95917c527/data')
df = pd.read_csv(project / 'spotify_analysis_dataset.csv')
all_cols = [str(col) for col in df.columns]

print("Columns in spotify_analysis_dataset.csv:")
for col in sorted(all_cols):
    print(f"  - {col}")

# Test column validation
msg = "Create a scatter plot of tempo vs valence from spotify_analysis_dataset.csv"
lower_msg = msg.lower()
lower_cols_map = {col.lower(): col for col in all_cols}

print(f"\nMessage: {msg}")
print(f"Lower: {lower_msg}")
print(f"Looking for 'vs' splits: {lower_msg.split(' vs ')}")

# Check if our test words are in the map
test_words = ["tempo", "valence"]
for word in test_words:
    print(f"'{word}' in lower_cols_map: {word in lower_cols_map}")

