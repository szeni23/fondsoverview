import pandas as pd
from datetime import datetime

csv_file = "deposit.csv"  # Adjust path if needed

# Create a new deposit entry with today's date and a fixed amount
today = datetime.today().strftime("%d.%m.%Y")
new_entry = pd.DataFrame([[today, 20]], columns=["date", "amount"])

try:
    # Try to load the existing CSV file
    df = pd.read_csv(csv_file, parse_dates=["date"], dayfirst=True)
    df = pd.concat([df, new_entry], ignore_index=True)
except FileNotFoundError:
    # If file doesn't exist, create a new one
    df = new_entry

# Save updated CSV
df.to_csv(csv_file, index=False)

print(f"Added new deposit entry: {today}, 20 CHF")