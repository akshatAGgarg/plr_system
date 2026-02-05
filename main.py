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

async def main(urls: list, build_id: str, mode: str = "complete", target_id: str = None, 
             auth_config: dict = None):
    print(f"Starting PLR for {len(urls)} URLs [Build: {build_id}]")
    
    import json
    SNAPSHOT_FILE = "last_snapshot.json"
    
    # Load or create baseline repository
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, 'r') as f:
            baseline_repo = json.load(f)
    else:
        baseline_repo = {}

    all_page_results = []
    
    async with DOMCapturer() as capturer:
        # 0. Optional Authentication
        if auth_config and auth_config.get("url"):
            await capturer.perform_login(
                auth_config["url"], 
                auth_config["username"], 
                auth_config["password"],
                auth_config.get("user_selector", "#username"),
                auth_config.get("pass_selector", "#password"),
                auth_config.get("submit_selector", "#login-btn")
            )

        for url in urls:
            print(f"\n--- Processing: {url} ---")
            
            # 1. Ingestion
            try:
                current_snapshot = await capturer.capture_page(url)
            except Exception as e:
                print(f"  - Capture failed for {url}: {e}")
                continue

            # Check for baseline
            old_snapshot = baseline_repo.get(url)
            
            if not old_snapshot:
                print(f"  - No baseline for {url}. Saving current state.")
                baseline_repo[url] = current_snapshot
                continue

            # 2. Analysis
            print("Step 2: Differential Analysis")
            differ = StructuralDiffer()
            diff_result = differ.diff(old_snapshot["dom_structure"], current_snapshot["dom_structure"])
            print(f"  - Edit Distance: {diff_result['distance']}")
            
            # 3. Discovery & Generation
            mutations_to_process = []
            stable_elements = []
            
            from integration.registry import LocatorRegistry
            registry = LocatorRegistry()
            tracked_keys = registry.registry.get("locators", {}).keys()

            for n1, n2 in diff_result['mapping']:
                if not n1: continue
                
                node_id = n1.attributes.get('id')
                node_classes = n1.classes
                
                match_key = None
                if node_id and node_id in tracked_keys:
                    match_key = node_id
                else:
                    for cls in node_classes:
                        dotted_cls = f".{cls}"
                        if dotted_cls in tracked_keys:
                            match_key = dotted_cls
                            break
                        for tk in tracked_keys:
                            if tk.startswith(".") and (tk[1:] in cls or cls in tk[1:]):
                                match_key = tk
                                break
                        if match_key: break
                
                if match_key:
                    if n1 != n2:
                        mutations_to_process.append((match_key, n1, n2))
                    else:
                        stable_elements.append((match_key, n1))

            if not mutations_to_process and not stable_elements:
                print("  - No tracked elements found on this page.")
                continue

            print(f"  - Summary: {len(mutations_to_process)} mutations, {len(stable_elements)} stable elements.")
            
            page_bundles = []
            from generator.bundle import LocatorBundleGenerator
            bundle_gen = LocatorBundleGenerator()
            new_root = Node.from_json(current_snapshot["dom_structure"])

            for key, n1, n2 in mutations_to_process:
                bundle = bundle_gen.generate_bundle(n2, new_root)
                page_bundles.append({"key": key, "old_node": n1, "bundle": bundle, "confidence": 0.98, "status": "REMEDIATED"})

            for key, n1 in stable_elements:
                page_bundles.append({"key": key, "old_node": n1, "bundle": {"primary": f"//*[@id='{n1.attributes.get('id')}']"}, "confidence": 1.0, "status": "STABLE"})

            all_page_results.append({"url": url, "results": page_bundles})

    # Save updated baseline
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(baseline_repo, f, default=lambda o: o.__dict__)

    # 4. Integration (Batch)
    remediations = []
    for page in all_page_results:
        for item in page['results']:
            if item['status'] == "REMEDIATED":
                remediations.append(item)
    
    if remediations:
        print(f"\nStep 4: Integration (GitOps Batch - {len(remediations)} updates)")
        from integration.registry import LocatorRegistry
        from integration.gitops import GitOpsBot
        registry = LocatorRegistry()
        bot = GitOpsBot()
        gitops_payload = []
        for item in remediations:
            registry.update_locator(item['key'], item['bundle']['primary'], confidence=item['confidence'])
            gitops_payload.append({
                "key": item['key'],
                "old": "N/A", # Simplified for batch
                "new": item['bundle']['primary'],
                "bundle": item['bundle'],
                "confidence": item['confidence']
            })
        bot.process_updates(gitops_payload)

    # 5. Reporting
    print("\nStep 5: Aggregated Reporting")
    full_report = "# PLR Aggregated Health Report\n"
    full_report += f"**Build:** {build_id} | **Timestamp:** {{timestamp}}\n\n"
    
    for page in all_page_results:
        full_report += f"### Page: {page['url']}\n"
        full_report += "| Status | Locator Key | New Selector | Confidence |\n"
        full_report += "|---|---|---|---|\n"
        for item in page['results']:
            status_label = "✅ STABLE" if item['status'] == "STABLE" else "🛠️ HEALED"
            full_report += f"| {status_label} | `{item['key']}` | `{item['bundle']['primary']}` | {int(item['confidence']*100)}% |\n"
        full_report += "\n"

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/plr_batch_{timestamp}.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report.format(timestamp=timestamp))
    with open("changes_report.md", "w", encoding="utf-8") as f:
        f.write(full_report.format(timestamp=timestamp))
        
    print(f"  - Generated batch report: '{report_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proactive Locator Remediation (PLR) - Batch Mode")
    parser.add_argument("--url", help="Single target URL")
    parser.add_argument("--urls", nargs="+", help="Multiple target URLs")
    parser.add_argument("--batch-file", help="File with list of URLs")
    parser.add_argument("--build", default="AUTO")
    # Auth Arguments
    parser.add_argument("--auth-url", help="Login page URL")
    parser.add_argument("--username", help="Login username")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--user-sel", default="#username")
    parser.add_argument("--pass-sel", default="#password")
    parser.add_argument("--submit-sel", default="#login-btn")
    
    args = parser.parse_args()
    
    target_urls = []
    if args.url: target_urls.append(args.url)
    if args.urls: target_urls.extend(args.urls)
    if args.batch_file and os.path.exists(args.batch_file):
        with open(args.batch_file, 'r') as f:
            target_urls.extend([line.strip() for line in f if line.strip()])
    
    if not target_urls:
        print("Error: No URLs provided.")
        sys.exit(1)
        
    auth_config = None
    if args.auth_url:
        auth_config = {
            "url": args.auth_url,
            "username": args.username,
            "password": args.password,
            "user_selector": args.user_sel,
            "pass_selector": args.pass_sel,
            "submit_selector": args.submit_sel
        }

    if args.build == "AUTO":
        import datetime
        args.build = datetime.datetime.now().strftime("%H%M")
        
    asyncio.run(main(target_urls, args.build, auth_config=auth_config))
