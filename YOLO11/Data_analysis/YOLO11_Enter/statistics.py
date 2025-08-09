import csv
from datetime import datetime

results = {
    "Total frames processed": 173,
    "Overall average confidence": 0.4127,
    "Exit status": "Resources released, program exited cleanly",
    "Processing date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

csv_file = "processing_results.csv"

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    writer.writerow(["Metric", "Value"])
    
    for key, value in results.items():
        writer.writerow([key, value])

print(f"Results successfully saved to {csv_file}")