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
            "https://sdtimes.com/category/software-quality/feed/",
            "http://feeds.feedburner.com/Testhead",
            "https://lisacrispin.com/feed/",
            "http://feeds.feedburner.com/blogspot/RLXA",
            "http://blog.aclairefication.com/feed/",
            "https://www.offsec.com/rss.xml?utm_source=offsec/",
            "https://visible-quality.blogspot.com/feeds/posts/default",
            # https://softwaretestingweekly.com/
            # https://www.testmuai.com/newsletter/editions/
            # https://atsqa.org/newsletter
            # ----------------------------------------------------------
            # podcasts
            "https://rss.libsyn.com/shows/79576/destinations/364260.xml"            
        ]
        self.keywords = ["backend", "api", "ai", "lead", "performance", "security", "architecture"]
        self.blacklist = ["/jobs/", "/vacancies/", "career", "hiring", "recruitment"]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        # self.session = requests.Session()

    def get_news(self) -> List[str]:
        final_news = []
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
      
        for url in self.feeds:
            source_news = []
            try:
                # Use requests to bypass blocking by User-Agent
                resp = requests.get(url, headers=self.headers, timeout=10)
                feed = feedparser.parse(resp.content)

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
                            
                            final_news.append({
                                'title': entry.title,
                                'link': entry.link,
                                'score': score,
                                'date': dt,
                            })
                
                source_news.sort(key=lambda x: (x['score'], x['date']), reverse=True)
                final_news.extend(source_news[:3])
                logger.info(f"Get {len(source_news[:3])} news from {url}")

            except Exception as e:
                logger.error(f"Source {url} not available (Timeout/Block). Skipped.")

        # Sort by keyword weight first, then by date
        final_news.sort(key=lambda x: (x['score'], x['date']), reverse=True)
        return final_news[:9]

    def send_to_telegram(self, message: str):
        if not self.token or not self.chat_id: return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }, timeout=10).raise_for_status()
        except Exception as e:
            logger.error(f"Telegram error: {e.response.text if hasattr(e, 'response') else e}")

    def run(self):
        news = self.get_news()
        if news:
            formatted = [f"{i+1}. <b>{html.escape(n['title'])}</b>\n{html.escape(n['link'])}" for i, n in enumerate(news)]
            header = f"🗞 <b>QA Trends (Balanced Selection)</b>\n\n"
            self.send_to_telegram(header + "\n\n".join(formatted))
        else:
            logger.warning("No new news found in 24 hours.")

if __name__ == "__main__":
    QANewsBot().run()
