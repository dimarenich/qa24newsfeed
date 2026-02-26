import os
import logging
import feedparser
import requests
import html
from typing import List
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QANewsBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.feeds = [
            "https://www.ministryoftesting.com/contents/rss",
            "https://feed.infoq.com/Testing/",
            "https://sdtimes.com/category/software-quality/feed/"
        ]
        self.keywords = ["backend", "api", "ai", "lead", "quality", "performance", "security", "architecture"]
        self.blacklist = ["/jobs/", "/vacancies/", "career", "hiring", "recruitment", "position"]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        # self.session = requests.Session()

    def get_news(self) -> List[str]:
        all_entries = []
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
      
        for url in self.feeds:
            try:
                # Use requests to bypass blocking by User-Agent
                resp = requests.get(url, headers=self.headers, timeout=15)
                feed = feedparser.parse(resp.content)
                
                source_count = 0
                for entry in feed.entries:
                    link = entry.link.lower()
                    title = entry.title.lower()

                    if any(word in link for word in self.blacklist) or any(word in title for word in self.blacklist):
                        continue

                    published = entry.get('published_parsed') or entry.get('updated_parsed')
                    if published:
                        dt = datetime(*published[:6], tzinfo=timezone.utc)
                        if dt > yesterday:
                            score = sum(5 for kw in self.keywords if kw in title)
                            
                            all_entries.append({
                                'title': entry.title,
                                'link': entry.link,
                                'score': score,
                                'date': dt,
                                'source': url
                            })
                            source_count += 1
                
                logger.info(f"{source_count} matching articles found for {url}")
            except Exception as e:
                logger.error(f"Parsing error {url}: {e}")

        # Sort by keyword weight first, then by date
        all_entries.sort(key=lambda x: (x['score'], x['date']), reverse=True)
        return all_entries[:9]

    def send_to_telegram(self, message: str):
        if not self.token or not self.chat_id: return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Telegram error: {e.response.text if hasattr(e, 'response') else e}")

    def run(self):
        news = self.get_news()
        if news:
            formatted = []
            for i, n in enumerate(news, 1):
                title = html.escape(n['title'])
                link = html.escape(n['link'])
                formatted.append(f"{i}. <b>{title}</b>\n{link}")
            
            header = f"🗞 <b>QA Trends & News (Top 9)</b>\n\n"
            self.send_to_telegram(header + "\n\n".join(formatted))
        else:
            logger.warning("No new news found in 24 hours.")

if __name__ == "__main__":
    bot = QANewsBot()
    bot.run()
