import csv
import json
import urllib.parse
import os
import requests
import time
import sys

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://shiseido.search.zetacx.net/api/item"

def get_product_api_details(shohin_pl_c_cd):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    params = {
        'q': shohin_pl_c_cd,
        'size': 1
    }
    try:
        r = requests.get(API_URL, params=params, headers=headers, verify=False, timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get('shohin_list', [])
            if items:
                return items[0]
    except Exception as e:
        print(f"Error fetching API details for {shohin_pl_c_cd}: {e}")
    return None

def convert_to_retail_json(row, api_details, top_category):
    category_name = row[0]
    raw_name = row[1]
    image_url = row[2]
    detail_url = row[3]
    
    parsed_url = urllib.parse.urlparse(detail_url)
    path_parts = parsed_url.path.split('/')
    product_id = ""
    if path_parts:
        filename = path_parts[-1]
        product_id = filename.replace('.html', '')
        
    if not product_id:
        product_id = raw_name
        
    title = raw_name
    brand = ""
    if raw_name.startswith('[') and ']' in raw_name:
        brand = raw_name[1:raw_name.index(']')]
        title = raw_name[raw_name.index(']')+1:].strip()
        
    categories = [top_category, category_name]
    
    # Correct Image CDN URL format
    final_image_url = ""
    if image_url:
        if "imagecdn.shiseido.co.jp" in image_url:
            final_image_url = image_url
        else:
            parsed_img = urllib.parse.urlparse(image_url)
            img_path = parsed_img.path.lstrip('/')
            if not img_path.startswith('resources/sw/'):
                img_path = f"resources/sw/{img_path}"
            final_image_url = f"https://imagecdn.shiseido.co.jp/c!/a=0,f=webp:jpg/{img_path}"

    product = {
        "id": product_id,
        "title": title,
        "brands": [brand] if brand else [],
        "categories": categories,
        "uri": detail_url,
        "images": [{"uri": final_image_url}] if final_image_url else []
    }
    
    if api_details:
        brand_mei = api_details.get('brnd_mei')
        if brand_mei:
            product["brands"] = [brand_mei]
            
        shohin_name = api_details.get('shohin_name')
        if shohin_name:
            product["title"] = shohin_name
            
        catch_copy = api_details.get('catch_copy_joho', '')
        product["description"] = catch_copy
        
        price_str = api_details.get('komi_kkk')
        if price_str:
            try:
                price = float(price_str)
                product["price_info"] = {
                    "currency_code": "JPY",
                    "price": price,
                    "original_price": price
                }
            except ValueError:
                pass
                
        attributes = {}
        
        gtin = api_details.get('sweb_shohin_cd')
        if gtin:
            product["gtin"] = gtin
            
        volume = api_details.get('hyoji_yo_naiyo_ryo')
        if volume:
            attributes["volume"] = {"text": [volume]}
            
        texture = api_details.get('type_zaikei_mei')
        if texture:
            attributes["texture"] = {"text": [texture]}
            
        yakuji = api_details.get('yakuji_kbn_mei')
        if yakuji:
            attributes["classification"] = {"text": [yakuji]}
            
        tags = api_details.get('hashtag', [])
        if tags:
            attributes["tags"] = {"text": tags}
            
        rating_str = api_details.get('heikin_hyoka')
        review_count_str = api_details.get('so_review_su')
        if rating_str:
            try:
                rating = float(rating_str)
                review_count = int(review_count_str) if review_count_str else 0
                attributes["rating"] = {"numbers": [rating]}
                attributes["review_count"] = {"numbers": [float(review_count)]}
            except ValueError:
                pass
                
        if attributes:
            product["attributes"] = attributes
            
    return product

def main():
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "skincare_products.csv"
    output_jsonl = sys.argv[2] if len(sys.argv) > 2 else "skincare_products.jsonl"
    
    # Map subcategories to their correct top-level categories
    category_mapping = {
        # Base Makeup
        "化粧下地": "ベースメイク",
        "ファンデーション": "ベースメイク",
        "BB・CC": "ベースメイク",
        "コンシーラー": "ベースメイク",
        "おしろい・フェイスパウダー": "ベースメイク",
        "トライアル・旅行用（ベースメイク）": "ベースメイク",
        "その他（ベースメイク）": "ベースメイク",
        # Sun Care
        "日焼け止め・ＵＶ": "サンケア",
        # Hair Care
        "シャンプー": "ヘアケア",
        "トリートメント・コンディショナー・リンス": "ヘアケア",
        "洗い流さないトリートメント": "ヘアケア",
        "頭皮ケア": "ヘアケア",
        "スタイリング": "ヘアケア",
        "ヘアカラー": "ヘアケア",
        "トライアル・旅行用（ヘア）": "ヘアケア",
        # Cosmetic Tools
        "ケース・ホルダー": "化粧用具",
        "スポンジ・パフ": "化粧用具",
        "チップ・ブラシ": "化粧用具",
        "クリーナー": "化粧用具",
        "アイラッシュカーラー": "化粧用具",
        "つけまつげ": "化粧用具",
        "シャープナー": "化粧用具",
        "毛抜き・眉ばさみ": "化粧用具",
        "あぶらとり紙・紙おしろい": "化粧用具",
        "かみそり": "化粧用具",
        "コットン・ティッシュ": "化粧用具",
        "その他（化粧用具）": "化粧用具",
        # Fragrance
        "香水・フレグランス・コロン": "フレグランス",
        "パフュームパウダー": "フレグランス",
        "ルームフレグランス": "フレグランス",
        # Baby
        "ベビー": "ベビー・キッズ",
        # Men's Face
        "男性用洗顔・シェービングフォーム": "メンズ",
        "男性用化粧水": "メンズ",
        "男性用乳液": "メンズ",
        "男性用保湿液": "メンズ",
        "男性用クリーム・男性用美容液": "メンズ",
        "男性用メイク": "メンズ",
        "男性用リップクリーム": "メンズ",
        "男性用トライアル・旅行用": "メンズ",
        # Men's Hair & Body
        "男性用シャンプー": "メンズ",
        "男性用コンディショナー": "メンズ",
        "男性用頭皮ケア": "メンズ",
        "男性用ヘアスタイリング・整髪料": "メンズ",
        "男性用汗対策": "メンズ",
        "男性用日焼け止め": "メンズ",
        "男性用ボディトリートメント・美容液": "メンズ",
        "その他（男性用ヘア・ボディ）": "メンズ",
        "男性用香水・フレグランス・コロン": "メンズ",
        # Health Food
        "サプリメント・健康食品": "健康食品",
        "その他（全体）": "その他"
    }

    # Deduce top-level category based on filename
    default_top_category = "スキンケア"
    if "makeup" in input_csv.lower():
        default_top_category = "ポイントメイク"
    elif "body" in input_csv.lower():
        default_top_category = "ボディ"
        
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return
        
    print(f"Converting {input_csv} -> {output_jsonl}...")
    count = 0
    
    with open(input_csv, mode='r', encoding='utf-8') as infile, \
         open(output_jsonl, mode='w', encoding='utf-8') as outfile:
         
        reader = csv.reader(infile)
        header = next(reader)
        
        for row in reader:
            if len(row) >= 4:
                category_name = row[0]
                # Determine the correct top category
                top_category = category_mapping.get(category_name, default_top_category)
                
                detail_url = row[3]
                parsed_url = urllib.parse.urlparse(detail_url)
                path_parts = parsed_url.path.split('/')
                product_id = ""
                if path_parts:
                    filename = path_parts[-1]
                    product_id = filename.replace('.html', '')
                
                api_details = None
                if product_id:
                    api_details = get_product_api_details(product_id)
                    time.sleep(0.1)
                    
                product_json = convert_to_retail_json(row, api_details, top_category)
                outfile.write(json.dumps(product_json, ensure_ascii=False) + "\n")
                count += 1
                if count % 50 == 0:
                    print(f"  Processed {count} products...")
                    
    print(f"Successfully converted {count} products to {output_jsonl}")

if __name__ == '__main__':
    main()
