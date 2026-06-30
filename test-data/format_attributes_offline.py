import json
import os
import sys

def format_offline(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    temp_path = file_path + ".tmp"
    converted_count = 0
    total_count = 0

    print(f"Offline formatting attributes in: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as infile, \
         open(temp_path, "w", encoding="utf-8") as outfile:
         
        for line_idx, line in enumerate(infile):
            line_str = line.strip()
            if not line_str:
                continue
                
            total_count += 1
            try:
                prod = json.loads(line_str)
            except Exception as e:
                print(f"Error parsing JSON on line {line_idx+1}: {e}")
                outfile.write(line + "\n")
                continue
                
            attributes = prod.get("attributes")
            # If attributes is a dictionary, convert it to a repeated record format
            if isinstance(attributes, dict):
                attributes_list = []
                for k, v in attributes.items():
                    attributes_list.append({
                        "key": k,
                        "value": v
                    })
                prod["attributes"] = attributes_list
                converted_count += 1
                
            outfile.write(json.dumps(prod, ensure_ascii=False) + "\n")

    # Replace original file with formatted file
    os.replace(temp_path, file_path)
    print(f"Completed offline formatting!")
    print(f"Total records read: {total_count}")
    print(f"Formatted records: {converted_count}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "/Users/minsoojun/work/VAIS_C/shiseido_data/all_products_with_price.jsonl"
    format_offline(target)
