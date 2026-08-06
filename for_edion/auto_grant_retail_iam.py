#!/usr/bin/env python3
"""
Auto Retail IAM Grant Tool for GECX & Retail Search
==================================================
Automatically discovers active GCP projects, GECX/Dialogflow service agents,
and all Service Accounts, then grants 'roles/retail.viewer' on the target project.
"""

import json
import os
import subprocess
import sys

# Target project where AI Commerce Search (Retail Search) resides
TARGET_PROJECT = "ai-commerce-search-e-osaka"
ROLES_TO_GRANT = ["roles/retail.viewer"]

def run_cmd(cmd):
    """Executes a command and returns stripped stdout, or empty string on failure."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()

def discover_service_accounts():
    sa_candidates = set()

    # 1. Local ADC file if configured
    adc_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if adc_path and os.path.exists(adc_path):
        try:
            with open(adc_path, "r") as f:
                data = json.load(f)
                if data.get("type") == "service_account" and "client_email" in data:
                    print(f"[+] Found SA in ADC file: {data['client_email']}")
                    sa_candidates.add(data["client_email"])
        except Exception as e:
            print(f"[!] Warning reading ADC file: {e}")

    # 2. Active gcloud account (if it's a Service Account)
    active_acc = run_cmd("gcloud config get-value account")
    if active_acc and active_acc.endswith(".gserviceaccount.com"):
        print(f"[+] Found active gcloud Service Account: {active_acc}")
        sa_candidates.add(active_acc)

    # 3. Currently configured gcloud project
    curr_proj = run_cmd("gcloud config get-value project")
    projects_to_scan = set([TARGET_PROJECT])
    if curr_proj:
        projects_to_scan.add(curr_proj)

    # 4. List all service accounts in candidate projects
    for proj in projects_to_scan:
        print(f"[*] Scanning Service Accounts in project [{proj}]...")
        out = run_cmd(f"gcloud iam service-accounts list --project={proj} --format=json")
        if out:
            try:
                sas = json.loads(out)
                for sa in sas:
                    email = sa.get("email")
                    if email:
                        print(f"    - Found SA: {email}")
                        sa_candidates.add(email)
            except Exception:
                pass

        # 5. Check GECX / CES / Dialogflow Service Agents by project number
        pnum = run_cmd(f"gcloud projects describe {proj} --format='value(projectNumber)'")
        if pnum:
            service_agents = [
                f"service-{pnum}@gcp-sa-ces.iam.gserviceaccount.com",
                f"service-{pnum}@gcp-sa-dialogflow.iam.gserviceaccount.com",
                f"service-{pnum}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
            ]
            for sa_agent in service_agents:
                sa_candidates.add(sa_agent)

    return sorted(list(sa_candidates))

def main():
    print("==================================================================")
    print(f" 🚀 Fully Automated Retail IAM Granting on Project: [{TARGET_PROJECT}]")
    print("==================================================================\n")

    candidates = discover_service_accounts()
    print(f"\n[+] Total Service Accounts/Agents identified: {len(candidates)}\n")

    granted_count = 0
    for sa in candidates:
        for role in ROLES_TO_GRANT:
            print(f"[*] Granting [{role}] -> [{sa}]...")
            cmd = f"gcloud projects add-iam-policy-binding {TARGET_PROJECT} --member='serviceAccount:{sa}' --role='{role}' --quiet"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"    ✅ SUCCESS: Granted {role} to {sa}")
                granted_count += 1
            else:
                if "does not exist" in res.stderr:
                    print(f"    ℹ️ SKIPPED: Service Account does not exist in GCP.")
                else:
                    print(f"    ⚠️ FAILED: {res.stderr.strip()}")

    print("\n==================================================================")
    print(f" 🎉 Completed! Total IAM bindings successfully updated: {granted_count}")
    print("==================================================================")

if __name__ == "__main__":
    main()
