import json
import os
import sys
import time
import requests
import re
import urllib3
from bs4 import BeautifulSoup

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_FILE = "/Users/minsoojun/work/VAIS_C/shiseido_data/all_products.jsonl"
OUTPUT_FILE = "/Users/minsoojun/work/VAIS_C/shiseido_data/all_products_with_price.jsonl"
API_URL = "https://www.shiseido.co.jp/sw/api/auth/V1/SWFR070220.seam"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json'
}

def clean_html(raw_html):
    if not raw_html:
        return ""
    # Replace br tags with newlines
    html = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    # Strip all other HTML tags
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    # Normalize multiple newlines/whitespace
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def process_all():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} does not exist.")
        return

    # Count total products
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)

    print(f"Total products to process: {total_lines}")
    print(f"Reading from: {INPUT_FILE}")
    print(f"Writing to: {OUTPUT_FILE}")

    processed_count = 0
    success_count = 0
    fail_count = 0
    start_time = time.time()

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            line_str = line.strip()
            if not line_str:
                continue

            try:
                prod = json.loads(line_str)
            except Exception as e:
                print(f"Error parsing JSON on line {processed_count+1}: {e}")
                continue

            prod_id = prod.get("id")
            if not prod_id:
                # If ID is missing, skip or log warning
                print(f"Warning: Product on line {processed_count+1} is missing 'id'. Skipping.")
                continue

            # Fetch product details from the API
            try:
                r = requests.get(API_URL, params={'shohin_pl_c_cd': prod_id}, headers=HEADERS, verify=False, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    
                    # 1. Price mapping (using camelCase)
                    price_str = data.get("komi_kkk")
                    if price_str:
                        try:
                            price = float(price_str)
                            prod["priceInfo"] = {
                                "currencyCode": "JPY",
                                "price": price,
                                "originalPrice": price
                            }
                        except ValueError:
                            print(f"Warning: Invalid price format '{price_str}' for ID {prod_id}")
                    
                    # 2. Description mapping
                    desc_html = data.get("body_copy_joho")
                    if desc_html:
                        prod["description"] = clean_html(desc_html)
                    else:
                        # Fallback to catch_copy_joho
                        catch_copy = data.get("catch_copy_joho")
                        if catch_copy:
                            prod["description"] = catch_copy

                    # 3. Extra Attributes mapping (list of key-value pairs for BigQuery Repeated Record)
                    attributes_list = []
                    
                    # Volume
                    volume = data.get('hyoji_yo_naiyo_ryo')
                    if volume:
                        attributes_list.append({
                            "key": "volume",
                            "value": {"text": [volume]}
                        })
                        
                    # Texture
                    texture = data.get('type_zaikei_mei')
                    if texture:
                        attributes_list.append({
                            "key": "texture",
                            "value": {"text": [texture]}
                        })
                        
                    # Classification (yakuji_kbn_mei)
                    classification = data.get('yakuji_kbn_mei')
                    if classification:
                        attributes_list.append({
                            "key": "classification",
                            "value": {"text": [classification]}
                        })
                        
                    # Country of origin
                    origin = data.get('gensan_koku')
                    if origin:
                        attributes_list.append({
                            "key": "countryOfOrigin",
                            "value": {"text": [origin]}
                        })
                    
                    if attributes_list:
                        prod["attributes"] = attributes_list

                    success_count += 1
                else:
                    print(f"Warning: API returned status {r.status_code} for product ID {prod_id}")
                    fail_count += 1
            except Exception as e:
                print(f"Error fetching API for ID {prod_id}: {e}")
                fail_count += 1

            # Write out the record regardless of API success (to preserve original record if API fails)
            outfile.write(json.dumps(prod, ensure_ascii=False) + "\n")

            processed_count += 1
            if processed_count % 50 == 0:
                elapsed = time.time() - start_time
                avg_speed = elapsed / processed_count
                remaining = (total_lines - processed_count) * avg_speed
                print(f"  Processed {processed_count}/{total_lines} ({processed_count/total_lines*100:.1f}%) | "
                      f"Success: {success_count}, Fail: {fail_count} | "
                      f"Avg: {avg_speed:.2f}s/prod | ETA: {remaining/60:.1f}m")

            # Small sleep to be polite
            time.sleep(0.05)

    total_time = time.time() - start_time
    print(f"\nCompleted processing!")
    print(f"Total time elapsed: {total_time/60:.2f} minutes")
    print(f"Total products processed: {processed_count}")
    print(f"Successful updates: {success_count}")
    print(f"Failed updates: {fail_count}")

if __name__ == '__main__':
    process_all()
