import asyncio
import argparse
import sys
import os

# Ensure terminal output handles UTF-8 (emojis etc)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ingest.capture import DOMCapturer
from analyze.diff import StructuralDiffer
from generator.robula import RobulaPlus
from integration.registry import LocatorRegistry
from integration.gitops import GitOpsBot
from common.models import Node

async def main(url: str, build_id: str, mode: str = "complete", target_id: str = None):
    print(f"Starting PLR for {url} [Build: {build_id}]")
    
    # 1. Ingestion
    capturer = DOMCapturer()
    print("Step 1: Ingestion (Launching Browser...)")
    try:
        current_snapshot = await capturer.capture_page(url)
        print(f"  - Captured {url}")
    except Exception as e:
        print(f"  - Capture failed: {e}")
        return

    # In a real scenario, we would fetch previous snapshot from DB.
    # For this demo, we will check if a local 'snapshot.json' exists to act as the "Old Build".
    # If not, we save this one and exit.
    import json
    
    SNAPSHOT_FILE = "last_snapshot.json"
    
    save_baseline = False
    
    if not os.path.exists(SNAPSHOT_FILE):
        print(f"  - No previous snapshot found. Saving current state as baseline to '{SNAPSHOT_FILE}'.")
        save_baseline = True
    else:
        with open(SNAPSHOT_FILE, 'r') as f:
            old_snapshot = json.load(f)
            
        # CHECK: Did the URL change?
        old_url = old_snapshot.get("url", "")
        if old_url != url:
            print(f"  - PROMPT: Target URL changed from '{old_url}' to '{url}'.")
            print(f"  - Resetting baseline for new target.")
            save_baseline = True
            
    if save_baseline:
        print("  - Saving baseline snapshot...")
        # Ensure we store the URL in the snapshot
        if "url" not in current_snapshot:
             current_snapshot["url"] = url
             
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(current_snapshot, f, default=lambda o: o.__dict__)
        return

    print("  - Found valid previous snapshot. Proceeding to Diff.")
    
    # Use the real captured data for new_snapshot
    new_snapshot = current_snapshot
    
    # 2. Analysis
    print("Step 2: Differential Analysis (RTED)")
    differ = StructuralDiffer()
    diff_result = differ.diff(old_snapshot["dom_structure"], new_snapshot["dom_structure"])
    print(f"  - Edit Distance: {diff_result['distance']}")
    
    # Identify broken locators based on diff mapping
    
    # 3. Discovery & Generation
    print(f"Step 3: Discovery & Generation (Mode: {mode})")
    
    mutations_to_process = []
    stable_elements = []
    
    if mode == "single":
        print(f"  - Tracking target ID: '{target_id}'")
        found = False
        for n1, n2 in diff_result['mapping']:
            if n1 and n1.attributes.get('id') == target_id:
                found = True
                if n1 != n2:
                    mutations_to_process.append((target_id, n1, n2))
                else:
                    stable_elements.append((target_id, n1))
                break
        if not found:
            print(f"  - Warning: Target ID '{target_id}' not found in previous snapshot.")
    else:
        # COMPLETE MODE: Scan mapping for nodes with ID or Class
        print("  - Scanning all elements for status...")
        for n1, n2 in diff_result['mapping']:
            if n1 and (n1.attributes.get('id') or n1.attributes.get('class')):
                # Use ID as key, fall back to class
                node_id = n1.attributes.get('id') or f".{n1.attributes.get('class')}"
                if n1 != n2:
                    mutations_to_process.append((node_id, n1, n2))
                else:
                    stable_elements.append((node_id, n1))

    if not mutations_to_process and not stable_elements:
        print("  - No tracked elements found on the page.")
        return

    print(f"  - Summary: {len(mutations_to_process)} mutations, {len(stable_elements)} stable elements.")
    
    all_bundles = []
    from generator.bundle import LocatorBundleGenerator
    bundle_gen = LocatorBundleGenerator()
    new_root = Node.from_json(new_snapshot["dom_structure"] if "dom_structure" in new_snapshot else new_snapshot)

    for key, n1, n2 in mutations_to_process:
        print(f"  - Remediating: {key}")
        bundle = bundle_gen.generate_bundle(n2, new_root)
        all_bundles.append({
            "key": key,
            "old_node": n1,
            "bundle": bundle,
            "confidence": 0.98,
            "status": "REMEDIATED"
        })

    # Process Stable (for reporting)
    for key, n1 in stable_elements:
        all_bundles.append({
            "key": key,
            "old_node": n1,
            "bundle": {"primary": f"//*[@id='{n1.attributes.get('id')}']"},
            "confidence": 1.0,
            "status": "STABLE"
        })

    # 4. Integration (Only for actual mutations)
    remediations = [b for b in all_bundles if b['status'] == "REMEDIATED"]
    if remediations:
        print(f"Step 4: Integration (GitOps Batch - {len(remediations)} updates)")
        registry = LocatorRegistry()
        bot = GitOpsBot()
        gitops_payload = []
        for item in remediations:
            registry.update_locator(item['key'], item['bundle']['primary'], confidence=item['confidence'])
            gitops_payload.append({
                "key": item['key'],
                "old": f"//*[@id='{item['old_node'].attributes.get('id')}']",
                "new": item['bundle']['primary'],
                "bundle": item['bundle'],
                "confidence": item['confidence']
            })
        bot.process_updates(gitops_payload)
    else:
        print("Step 4: Integration (Skipped - No mutations)")
    
    # 5. Reporting
    print("Step 5: Reporting")
    report_rows = ""
    
    # Sort: Healed first
    all_bundles.sort(key=lambda x: x['status'] == 'STABLE')

    for item in all_bundles:
        if item['status'] == "STABLE":
            continue
            
        key = item['key']
        old_node = item['old_node']
        
        # Defensive check: ensure Node object
        if old_node and isinstance(old_node, dict):
            old_node = Node.from_json(old_node)
            
        if old_node:
            if old_node.attributes.get('id'):
                old_xpath = f"//*[@id='{old_node.attributes.get('id')}']"
            else:
                old_xpath = f"//{old_node.tag}[@class='{old_node.attributes.get('class', 'unknown')}']"
        else:
            old_xpath = "N/A (New)"
            
        new_xpath = item['bundle'].get('primary', 'N/A')
        status_label = "✅ STABLE" if item['status'] == "STABLE" else "🛠️ HEALED"
        report_rows += f"| {status_label} | `{key}` | `{old_xpath}` | `{new_xpath}` | {int(item['confidence']*100)}% |\n"

    report_content = f"""# PLR Health Report
**Build:** {build_id}
**Timestamp:** {{timestamp}}
**URL:** {url}
**Status:** {"⚠️ PATCHED" if remediations else "✅ STABLE"}

## Tracking Summary
| Status | Locator Key | Old Selector | New Selector | Confidence |
|---|---|---|---|---|
{report_rows}

*Report generated by PLR System*
"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/plr_report_{timestamp}.md"
    
    # Use UTF-8 for all file operations to avoid Windows charmap errors
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content.format(timestamp=timestamp))
        
    with open("changes_report.md", "w", encoding="utf-8") as f:
        f.write(report_content.format(timestamp=timestamp))
        
    print(f"  - Generated archived report: '{report_path}'")
    print("  - Updated 'changes_report.md'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proactive Locator Remediation (PLR) - Enterprise Health Check")
    parser.add_argument("--url", required=True, help="The target URL to scan (e.g. https://example.com)")
    parser.add_argument("--build", default="AUTO", help="Build Identifier (e.g. 101, staging-v4)")
    parser.add_argument("--target-id", default=None, help="The specific ID to track (if using single mode)")
    parser.add_argument("--mode", choices=["single", "complete"], default="complete", help="Operation mode (defaults to complete)")
    args = parser.parse_args()
    
    # If no build ID provided, generate one based on timestamp
    if args.build == "AUTO":
        import datetime
        args.build = datetime.datetime.now().strftime("%H%M")
        
    asyncio.run(main(args.url, args.build, args.mode, args.target_id))
