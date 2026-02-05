import asyncio
import json
import os
from playwright.async_api import async_playwright, Page, Playwright

class DOMCapturer:
    def __init__(self):
        self._browser = None
        self._context = None
        self._playwright = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def perform_login(self, auth_url: str, username: str, password: str, 
                        user_selector: str = "#username", 
                        pass_selector: str = "#password", 
                        submit_selector: str = "#login-btn"):
        """
        Navigates to auth_url, fills credentials and submits.
        """
        print(f"    [Auth] Attempting login at {auth_url}")
        page = await self._context.new_page()
        await page.goto(auth_url, wait_until="networkidle")
        
        await page.fill(user_selector, username)
        await page.fill(pass_selector, password)
        await page.click(submit_selector)
        
        await page.wait_for_load_state("networkidle")
        print(f"    [Auth] Login submitted. Current URL: {page.url}")
        await page.close()

    async def capture_page(self, url: str):
        # Ensure we have a context if not using context manager
        close_on_finish = False
        if not self._context:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context()
            close_on_finish = True

        page = await self._context.new_page()
        
        await page.goto(url, wait_until="networkidle")
        
        # 1. Wait for Hydration (Beacon)
        from ingest.beacon import HV_BEACON_SCRIPT
        print(f"    [Ingest] Capturing {url}...")
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
                    
                    if (node.childNodes) {
                        for (let i = 0; i < node.childNodes.length; i++) {
                            obj.children.push(serializeNode(node.childNodes[i]));
                        }
                    }
                    
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
        await page.close()
        
        if close_on_finish:
            await self._browser.close()
            await self._playwright.stop()
            
        return {
            "url": url,
            "ax_tree": ax_tree,
            "dom_structure": clean_dom,
            "raw_structure": dom_snapshot,
            "html_content": content 
        }

if __name__ == "__main__":
    async def main():
        async with DOMCapturer() as capturer:
            result = await capturer.capture_page("https://example.com")
            print(f"Captured DOM Root: {result['dom_structure']['nodeName']}")
            
    asyncio.run(main())
