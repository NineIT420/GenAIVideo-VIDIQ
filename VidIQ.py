import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class VidIQLogin():
    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASS")
        self.page = None
        self.context = None
        self.browser = None
        self.pw = None
        self.user_data_dir = os.path.abspath("vidiq_user_data")

    @classmethod
    async def create(cls):
        self = cls()
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ],
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
        return self

    async def login_to_email(self):
        """Login to email account first (for verification)"""
        try:
            print("Logging in to email account...")

            await self.page.goto("https://mail.google.com", wait_until="networkidle")
            await self.page.fill('input[type="email"]', self.email_user)
            await self.page.click('#identifierNext')
            await self.page.wait_for_timeout(2000)
            await self.page.fill('input[type="password"]', self.email_pass)
            await self.page.click('#passwordNext')
            await self.page.wait_for_timeout(5000)
            print("Email login completed. Check for any VidIQ verification emails.")
            return True
        except Exception as e:
            print(f"Email login failed: {str(e)}")
            return False
  
    async def login_to_vidiq(self):
        """Login to VidIQ account"""
        try:
            print("Logging in to VidIQ...")
            await self.page.goto("https://app.vidiq.com/auth/login", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(5000)
            google_button = await self.page.query_selector('button:has-text("with Google")')
            if not google_button:
                print("❌ Google login button not found. Taking screenshot.")
                await self.page.screenshot(path="vidiq_google_button_not_found.png")
                return False
            print("✅ Found Google login button. Clicking...")
            async with self.browser.expect_page() as popup_info:
                await google_button.click()
            google_page = await popup_info.value
            await google_page.wait_for_load_state('domcontentloaded')
            await google_page.wait_for_timeout(3000)
            accounts = await google_page.query_selector_all('div[data-identifier]')
            if accounts:
                print("✅ Google account(s) found. Clicking on first account...")
                await accounts[0].click()
            else:
                print("⚠️ No saved account, proceeding with manual login...")
                return False
            try:
                print("🔍 Waiting for 'Skip1' button...")
                skip_button = await self.page.wait_for_selector('button:has-text("Skip")', timeout=5000)
                if skip_button:
                    print("➡️ Clicking 'Skip1'...")
                    await skip_button.click()
                    await self.page.wait_for_timeout(3000)
            except PlaywrightTimeout:
                print("⏭️ 'Skip1' button not shown. Continuing...")
            try:
                print("🔍 Waiting for 'Skip2' button...")
                skip_button = await self.page.wait_for_selector('button:has-text("Skip")', timeout=5000)
                if skip_button:
                    print("➡️ Clicking 'Skip2'...")
                    await skip_button.click()
                    await self.page.wait_for_timeout(3000)
            except PlaywrightTimeout:
                print("⏭️ 'Skip2' button not shown. Continuing...")    
            try:
                print("🔍 Looking for checkout modal close button...")
                svg = await self.page.wait_for_selector("svg.lucide-x", timeout=5000)
                button_handle = await svg.evaluate_handle("""
                    el => el.closest('button') || el.closest('[role="button"]') || el.parentElement
                """)
                button = button_handle.as_element()
                if button:
                    print("➡️ Attempting to click the clickable parent of SVG...")
                    await button.click()
                    await self.page.wait_for_timeout(5000)
                    print("✅ Checkout modal closed.")
                else:
                    print("⚠️ No clickable parent found, trying to click SVG directly...")
                    await svg.click()
                    await self.page.wait_for_timeout(5000)
                    print("✅ SVG clicked directly.")
            except PlaywrightTimeout:
                print("⏭️ Checkout close button not found. Skipping...")
            except Exception as e:
                print(f"❌ Error clicking close button: {e}")
            try:
                print("🔍 Waiting for 'Skip3' button...")
                skip_button = await self.page.wait_for_selector('button:has-text("Skip")', timeout=5000)
                if skip_button:
                    print("➡️ Clicking 'Skip3'...")
                    await skip_button.click()
                    await self.page.wait_for_timeout(5000)
            except PlaywrightTimeout:
                print("⏭️ 'Skip3' button not shown. Continuing...")   

            await self.page.wait_for_url("https://app.vidiq.com/dashboard", timeout=3000)
            print("✅ VidIQ login successful")
            return True
        except PlaywrightTimeout:
            print("⏰ VidIQ login timeout - check for CAPTCHA or verification needs")
            await self.page.screenshot(path="vidiq_login_timeout.png")
            return False
        except Exception as e:
            print(f"❌ VidIQ login failed: {str(e)}")
            return False

    async def is_logged_in(self):
        try:
            await self.page.goto("https://app.vidiq.com/dashboard", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(5000)
            if "login" in self.page.url.lower():
                return False
            return self.page
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            return False

    def clean_text(self, text):
        text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII characters
        text = re.sub(r"\s+", " ", text).strip()    # Normalize whitespace
        return text

    def clean_state(self, text):
        text = text.replace("•", ",")  # Replace bullet with comma
        text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove other non-ASCII
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def find_trending_videos(self, page, keyword):
        try:
            button = page.get_by_role("link", name="Find Trending Videos").first
            await button.click(timeout=3000)
            print("✅ Find Trending Videos Clicked using role-based locator")
            await page.wait_for_timeout(3000)
        except Exception as e2:
                    print(f"Role-based locator failed: {str(e2)[:100]}... Trying final fallback")
        try:
            search_input = page.get_by_placeholder("Search")
            await search_input.fill(keyword)
            await search_input.press("Enter")
            print(f"✅ Typed '{keyword}' into search bar")
        except Exception as e3:
            print(f"❌ Failed to type in search bar: {str(e3)[:100]}")
        await page.wait_for_timeout(5000)
        html = await page.content()
        soup = BeautifulSoup(await page.content(), "html.parser")
        results = []
        # Each card is its own container; collect them all
        cards = soup.find_all("div", class_="flex h-full flex-col px-medium py-2xsmall")
        if not cards:
            print("❌ Could not find any video cards.")
            return results
        for card in cards:
            title = None
            channel_info = None
            stats = None
            vph_freemium = None
            multiplier = None
            video_url = None
            # Title
            title_tag = card.find("p", class_="text-1 antialiased text-lg font-bold text-left line-clamp-2")
            if title_tag:
                title = title_tag.get_text(strip=True)
            # Channel and subscribers, then views and age
            info_tags = card.find_all("p", class_="text-2 antialiased text-xs font-bold text-left")
            if len(info_tags) >= 2:
                channel_info = info_tags[0].get_text(" ", strip=True)
                stats = info_tags[1].get_text(" ", strip=True)
            # Multiplier (e.g. 26x)
            multiplier_tag = card.find("div",
                                        class_=lambda c: c and
                                        "min-w-[4ch]" in c and
                                        "rounded-full" in c and
                                        "py-3xsmall" in c and
                                        "px-xsmall" in c
                                        )
            if multiplier_tag:
                multiplier = multiplier_tag.get_text(strip=True)
            # VPH (e.g. 134 VPH)
            vph_tag = card.find("div", class_="bg-elevated-1 rounded-full py-[2px] px-xsmall")
            if vph_tag:
                vph_freemium = vph_tag.get_text(strip=True)
            # Try to get the YouTube video ID from the thumbnail style background
            thumbnail_div = card.find_previous("div", style=lambda x: x and "i.ytimg.com/vi_webp" in x)
            if thumbnail_div:
                match = re.search(r"vi_webp/([a-zA-Z0-9_-]{11})/hqdefault\.webp", thumbnail_div.get("style", ""))
                if match:
                    video_id = match.group(1)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
            if title:
                results.append({
                    "title": self.clean_text(title),
                    "video_url": video_url,
                    "stats": self.clean_state(stats) if stats else None,
                    "VPH": self.clean_text(vph_freemium) if vph_freemium else None,
                    "VidIQ_Score": self.clean_text(multiplier) if multiplier else None,
                })
        print(f"✅ Extracted {len(results)} videos.")
        if not results:
            print("❌ No videos found. Check if the search term is correct or if the page structure has changed.")
            return results
        return results

    async def find_keywords(self, page, keyword):
        try:
            button = page.get_by_role("link", name="Find Trending Keywords").first
            await button.click(timeout=3000)
            print("✅ Find Trending Keywords Clicked using role-based locator")
            await page.wait_for_timeout(3000)
        except Exception as e3:
                    print(f"Role-based locator failed: {str(e3)[:100]}... Trying final fallback")
        try:
            search_input = page.get_by_placeholder("Search")
            await search_input.fill(keyword)
            await search_input.press("Enter")
            print(f"✅ Typed '{keyword}' into search bar")
        except Exception as e3:
            print(f"❌ Failed to type in search bar: {str(e3)[:100]}")
        await page.wait_for_timeout(5000)
        html = await page.content()
        soup = BeautifulSoup(await page.content(), "html.parser")
        container = soup.find("div", class_="css-u6v8er")
        if container:
            score = container.find("span", {"data-testid": "gauge-overall-score"}).text
            score_label = container.find("p", {"data-testid": "gauge-overall-score-label"}).text
            search_volume = container.find("p", {"data-testid": "gauge-search-volume"}).text
            search_label = container.find("span", {"data-testid": "gauge-search-volume-label"}).text
            competition = container.find("p", {"data-testid": "gauge-competition"}).text
            competition_label = container.find("span", {"data-testid": "gauge-competition-label"}).text
            results = {
                "score": score,
                "score_label": score_label,
                "search_volume": search_volume,
                "search_label": search_label,
                "competition": competition,
                "competition_label": competition_label
            }
        else:
            print("❌ Element with class 'css-u6v8er' not found.")
        if not results:
            print("❌ No results.")
            return results
        return results