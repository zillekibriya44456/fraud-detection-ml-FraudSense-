import pandas as pd
import json
import os

datasets = [
    {
        "name": "ULB Credit Card",
        "path": "data/raw/creditcard.csv",
        "target": "Class"
    },
    {
        "name": "UPI Fraud",
        "path": "data/raw/fraud_dataset.csv",
        "target": "is_fraud"
    },
    {
        "name": "PaySim",
        "path": "data/raw/PS_20174392719_1491204439457_log.csv",
        "target": "isFraud"
    },
    {
        "name": "IEEE-CIS Transaction",
        "path": "data/raw/IEEE_CIS archive (3)/train_transaction.csv",
        "target": "isFraud"
    },
    {
        "name": "IEEE-CIS Identity",
        "path": "data/raw/IEEE_CIS archive (3)/train_identity.csv",
        "target": None
    }
]

results = {}

for ds in datasets:
    path = ds["path"]
    name = ds["name"]
    target = ds["target"]
    
    if not os.path.exists(path):
        print(f"{name} not found at {path}")
        continue
        
    file_size = os.path.getsize(path) / (1024 * 1024)
    print(f"Processing {name} ({file_size:.2f} MB)...")
    
    total_rows = 0
    missing_values = 0
    fraud_count = 0
    legit_count = 0
    columns = []
    
    try:
        # Read in chunks to save memory
        chunk_iter = pd.read_csv(path, chunksize=100000, low_memory=False)
        first_chunk = True
        
        for chunk in chunk_iter:
            if first_chunk:
                columns = list(chunk.columns)
                first_chunk = False
            
            total_rows += len(chunk)
            missing_values += chunk.isna().sum().sum()
            
            if target and target in chunk.columns:
                counts = chunk[target].value_counts()
                legit_count += counts.get(0, 0)
                fraud_count += counts.get(1, 0)
                
        results[name] = {
            "file_size_mb": round(file_size, 2),
            "total_rows": int(total_rows),
            "num_columns": len(columns),
            "missing_values": int(missing_values),
            "target": target if target in columns else "Not Found",
            "legit_count": int(legit_count),
            "fraud_count": int(fraud_count),
            "fraud_percentage": round((fraud_count / total_rows * 100), 4) if total_rows > 0 and target else None,
            "columns": columns
        }
    except Exception as e:
        print(f"Error processing {name}: {e}")

with open('dataset_stats.json', 'w') as f:
    json.dump(results, f, indent=4)
print("Done writing to dataset_stats.json")
