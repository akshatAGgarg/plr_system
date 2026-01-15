import asyncio
import json
from playwright.async_api import async_playwright, Page, Playwright

class DOMCapturer:
    async def capture_page(self, url: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle")
            
            # 1. Wait for Hydration (Beacon)
            from ingest.beacon import HV_BEACON_SCRIPT
            print("    [Ingest] Waiting for hydration...")
            try:
                # Inject and wait for the promise to resolve
                reason = await page.evaluate(HV_BEACON_SCRIPT)
                print(f"    [Ingest] Hydration complete. Reason: {reason}")
            except Exception as e:
                print(f"    [Ingest] Hydration warning: {e}")

            # 2. Capture CDP Session
            client = await page.context.new_cdp_session(page)
            
            # 3. Get AXTree
            ax_tree = await client.send("Accessibility.getFullAXTree")
            
            # 4. Flattened DOM with Shadow Roots
            # We inject a script to traverse the DOM including shadow roots
            # This is a recursive function to build a JSON representation
            dom_snapshot = await page.evaluate("""
                () => {
                    function serializeNode(node) {
                        const obj = {
                            nodeName: node.nodeName,
                            nodeType: node.nodeType,
                            nodeValue: node.nodeValue,
                            attributes: {},
                            children: []
                        };
                        
                        if (node.attributes) {
                            for (let i = 0; i < node.attributes.length; i++) {
                                const attr = node.attributes[i];
                                obj.attributes[attr.name] = attr.value;
                            }
                        }
                        
                        // Serialize children
                        if (node.childNodes) {
                            for (let i = 0; i < node.childNodes.length; i++) {
                                obj.children.push(serializeNode(node.childNodes[i]));
                            }
                        }
                        
                        // Handle Shadow DOM
                        if (node.shadowRoot) {
                            obj.shadowRoot = serializeNode(node.shadowRoot);
                        }
                        
                        return obj;
                    }
                    return serializeNode(document.documentElement);
                }
            """)
            
            # 5. Clean DOM (Dynamic Attribute Masking)
            from ingest.cleaner import DOMCleaner
            cleaner = DOMCleaner()
            clean_dom = cleaner.clean(dom_snapshot)
            
            content = await page.content()
            
            await browser.close()
            
            return {
                "url": url,
                "ax_tree": ax_tree,
                "dom_structure": clean_dom, # Return clean structure
                "raw_structure": dom_snapshot, # Keep raw if needed
                "html_content": content 
            }

if __name__ == "__main__":
    # Test execution
    async def main():
        capturer = DOMCapturer()
        result = await capturer.capture_page("https://example.com")
        print(f"Captured AXTree Nodes: {len(result['ax_tree']['nodes'])}")
        print(f"Captured DOM Root: {result['dom_structure']['nodeName']}")
        
    asyncio.run(main())
