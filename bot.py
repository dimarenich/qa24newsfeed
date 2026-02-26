import os
import logging
import feedparser
import requests
import html
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
                    # escaping special characters for HTML
                    title = html.escape(entry.title)
                    link = html.escape(entry.link)
                    news_items.append(f"<b>{title}</b>\n{link}")
            except Exception as e:
                logger.error(f"Parsing error {url}: {e}")
        return news_items[:9]

    def send_to_telegram(self, message: str):
        if not self.token or not self.chat_id:
            logger.error("The TELEGRAM_TOKEN or CHAT_ID environment variables are not set.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("The message has been successfully sent to Telegram.")
        except requests.exceptions.RequestException as e:
            # Display Telegram error details in logs
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"Error sending to Telegram: {error_detail}")

    def run(self):
        logger.info("Launching news collection...")
        news = self.get_top_news()
        if news:
            header = f"🗞 <b>QA Summary ({datetime.now().strftime('%Y-%m-%d')})</b>\n\n"
            self.send_to_telegram(header + "\n\n".join(news))
        else:
            logger.warning("No new news found.")

if __name__ == "__main__":
    bot = QANewsBot()
    bot.run()
