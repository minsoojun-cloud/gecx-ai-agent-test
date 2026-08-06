import os
import json

transcript_path = "/Users/minsoojun/.gemini/jetski/brain/1136d1e3-f4a7-4922-b071-5d0dfc2b398d/.system_generated/logs/transcript_full.jsonl"
if os.path.exists(transcript_path):
    print("Scanning...")
    with open(transcript_path, 'r') as f:
        # Find all browser subagent steps and print the most recent one
        subagent_steps = []
        for idx, line in enumerate(f):
            if '"type":"BROWSER_SUBAGENT"' in line:
                subagent_steps.append((idx + 1, line))
        
        if subagent_steps:
            last_idx, last_line = subagent_steps[-1]
            print(f"Found last subagent step at line {last_idx}:")
            try:
                obj = json.loads(last_line)
                print("Content:")
                print(obj.get("content"))
            except Exception as e:
                print("Error parsing JSON:", e)
        else:
            print("No subagent steps found.")
else:
    print("Transcript not found.")
