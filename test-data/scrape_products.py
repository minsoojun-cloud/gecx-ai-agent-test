import csv
import urllib.parse
import time
import os
import requests

INPUT_CSV = "skincare_categoly.csv"
OUTPUT_CSV = "skincare_products.csv"
API_URL = "https://shiseido.search.zetacx.net/api/item"

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_products_via_api(category_name, category_url):
    print(f"Scraping category via API: {category_name}")
    products = []
    
    # Parse category parameters from the URL
    parsed_url = urllib.parse.urlparse(category_url)
    params = urllib.parse.parse_qs(parsed_url.query)
    
    shohin_ctgry_cd = params.get('shohin_ctgry_cd', [''])[0]
    birui_cd = params.get('birui_cd', [''])[0]
    
    if not shohin_ctgry_cd:
        print(f"  Could not parse shohin_ctgry_cd from {category_url}")
        return []
        
    page = 1
    page_size = 30
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.shiseido.co.jp',
        'Referer': category_url
    }
    
    while True:
        offset = (page - 1) * page_size
        query_params = {
            'size': page_size,
            'offset': offset,
            'shohin_ctgry_cd_j': shohin_ctgry_cd,
        }
        if birui_cd:
            query_params['birui_cd_j'] = birui_cd
            
        print(f"  Fetching Page {page} (offset: {offset})...")
        try:
            response = requests.get(API_URL, params=query_params, headers=headers, verify=False, timeout=10)
            if response.status_code != 200:
                print(f"    Error: API returned status {response.status_code}")
                break
                
            data = response.json()
            items = data.get('shohin_list', [])
            total = int(data.get('total', 0))
            
            if not items:
                print("    No more items found.")
                break
                
            print(f"    Found {len(items)} items (Total: {total})")
            for item in items:
                # Extract brand and name
                brand = item.get('brnd_mei', '')
                name = item.get('shohin_name', '')
                if brand and name:
                    product_name = f"[{brand}] {name}"
                else:
                    product_name = name or item.get('shohin_pl_c_mei', 'Unknown Product')
                
                # Image URL
                # CDN format: https://imagecdn.shiseido.co.jp/c!/a=0,f=webp:jpg/resources/sw/products/img/...
                image_path = item.get('shohin_pl_c_gz_ir_fl_pth', '')
                if image_path:
                    # Strip leading slashes to avoid issues
                    clean_path = image_path.lstrip('/')
                    # In some cases, the path might already contain 'resources/sw/' or just 'products/img/'
                    # Let's ensure the format is correct
                    if not clean_path.startswith('resources/sw/'):
                        clean_path = f"resources/sw/{clean_path}"
                    image_url = f"https://imagecdn.shiseido.co.jp/c!/a=0,f=webp:jpg/{clean_path}"
                else:
                    image_url = ""
                
                # Detail URL
                # The detail URL usually goes to /products/{shohin_pl_c_cd}.html
                shohin_pl_c_cd = item.get('shohin_pl_c_cd', '')
                if shohin_pl_c_cd:
                    detail_url = f"https://www.shiseido.co.jp/sw/onlinestore/products/{shohin_pl_c_cd}.html"
                else:
                    detail_url = ""
                
                products.append({
                    'Category': category_name,
                    'Product Name': product_name,
                    'Image URL': image_url,
                    'Detail URL': detail_url
                })
                
            if len(products) >= total or len(items) < page_size:
                break
                
            page += 1
            time.sleep(0.5) # Polite delay
        except Exception as e:
            print(f"    Error requesting API: {e}")
            break
            
    return products

def main():
    import sys
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "skincare_categoly.csv"
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "skincare_products.csv"
    
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return
        
    all_products = []
    with open(input_csv, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader) # skip header
        for row in reader:
            if len(row) >= 2:
                cat_name, cat_url = row[0], row[1]
                products = fetch_products_via_api(cat_name, cat_url)
                all_products.extend(products)
                time.sleep(0.5)
                
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Category', 'Product Name', 'Image URL', 'Detail URL'])
        writer.writeheader()
        writer.writerows(all_products)
    print(f"Successfully saved {len(all_products)} products to {output_csv}")

if __name__ == '__main__':
    main()
