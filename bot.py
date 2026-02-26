import os
import logging
import feedparser
import requests
from typing import List
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
        self.session = requests.Session()

    def get_top_news(self) -> List[str]:
        news_items = []
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                if feed.entries:
                    entry = feed.entries[0]
                    news_items.append(f"🔹 *{entry.title}*\n{entry.link}")
            except Exception as e:
                logger.error(f"Parsing error {url}: {e}")
        return news_items[:9]

    def send_to_telegram(self, message: str):
        if not self.token or not self.chat_id:
            logger.error("The TELEGRAM_TOKEN or CHAT_ID environment variables are not set.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            response = self.session.post(
                url, 
                json={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("The message has been successfully sent to Telegram.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to Telegram: {e}")

    def run(self):
        logger.info("Launching news collection...")
        news = self.get_top_news()
        if news:
            header = f"🗞 *QA Summary ({datetime.now().strftime('%Y-%m-%d')})*\n\n"
            self.send_to_telegram(header + "\n\n".join(news))
        else:
            logger.warning("No new news found.")

if __name__ == "__main__":
    bot = QANewsBot()
    bot.run()
