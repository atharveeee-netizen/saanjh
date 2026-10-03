import os
import urllib.request
import zipfile
import hashlib
import json
import time

def download_uci_dataset():
    """Downloads the UCI Individual Household Electric Power Consumption dataset."""
    url = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'raw', 'real'))
    os.makedirs(raw_dir, exist_ok=True)
    
    zip_path = os.path.join(raw_dir, 'household_power_consumption.zip')
    
    # 1. Download with retry
    print(f"Downloading dataset from {url}...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
            print("Download successful.")
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                print("All download attempts failed.")
                return False
            time.sleep(2)
            
    # 2. Calculate SHA256 Checksum
    sha256_hash = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    print(f"File SHA-256: {checksum}")
    
    # 3. Extract
    print("Extracting dataset...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(raw_dir)
        print("Extraction complete.")
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False
        
    # 4. Save metadata
    metadata = {
        "dataset": "UCI Individual Household Electric Power Consumption",
        "source": "UCI Machine Learning Repository",
        "url": url,
        "download_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sha256_checksum": checksum,
        "extracted_files": os.listdir(raw_dir),
        "license": "Open Data / Public Domain",
        "resolution": "1-minute",
        "notes": "Data is highly detailed but missing some Indian geographic relevance. Being used purely to train forecasting methodology."
    }
    
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'real_data'))
    os.makedirs(artifacts_dir, exist_ok=True)
    with open(os.path.join(artifacts_dir, 'dataset_manifest.json'), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print("Metadata saved. Download pipeline complete.")
    return True

if __name__ == "__main__":
    download_uci_dataset()
