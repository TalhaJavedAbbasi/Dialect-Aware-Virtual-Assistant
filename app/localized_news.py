import os
import requests
from bs4 import BeautifulSoup
from flask_login import current_user
#from gnews import GNews
import feedparser

# API Key (Use an environment variable for security)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

EVENTBRITE_API_KEY = os.getenv("EVENTBRITE_API_KEY")
EVENTBRITE_API_URL = "https://www.eventbriteapi.com/v3/events/search/"

if not EVENTBRITE_API_KEY:
    print("Error: Missing Eventbrite API Key. Please check your .env file.")
print(EVENTBRITE_API_KEY)
# Example Urdu and English news RSS feed URLs (update with valid feeds)
URDU_NEWS_FEEDS = [
    "https://www.bbc.com/urdu/index.xml",  # BBC Urdu
    "https://urdu.geo.tv/rss/1/0",  # Geo News Urdu
    "https://www.express.pk/feed/"  # Express News Urdu
]

ENGLISH_NEWS_FEEDS = [
    "https://news.google.com/news/rss",  # Google News English
    "https://rss.cnn.com/rss/cnn_topstories.rss",  # CNN Top Stories
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"  # NY Times
]

def format_news(articles, language="ur"):
    """
    Formats news articles into a simple text response with language-specific link text.
    :param articles: List of article dictionaries
    :param language: ('ur' for Urdu, 'en' for English)
    :return: List of formatted news strings
    """
    news_list = []
    link_text = "مزید پڑھیں" if language == "ur" else "Read more"  # Set the appropriate link text

    for article in articles:
        title = article.get("title", "No title")
        url = article.get("link", "#")  # Ensuring link availability
        news_list.append(f"🔹 {title} – [{link_text}]({url})")

    return news_list if news_list else ["معذرت! کوئی خبر دستیاب نہیں۔" if language == "ur" else "Sorry! No news available."]

def fetch_urdu_news(topic=None):
    """
    Fetches Urdu news headlines from RSS feeds with optional topic filtering.
    :param topic: (Optional) Fetch only news related to a specific topic (e.g., "sports").
    :return: Formatted Urdu news headlines.
    """
    all_news = []

    for feed_url in URDU_NEWS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Fetch top 5 news per source
            title = entry.get("title", "No title available")
            link = entry.get("link", "#")

            # If a topic is provided, filter news based on the topic keyword
            if topic and topic.lower() not in title.lower():
                continue

            all_news.append({"title": title, "link": link})

    if all_news:
        formatted_news = "\n\n".join(format_news(all_news, language="ur"))
        return f"<strong>:یہ ہیں آج کی تازہ خبریں</strong>\n\n{formatted_news}"  # Heading in Urdu
    return "معذرت! کوئی خبر دستیاب نہیں۔"

# def fetch_urdu_news(topic=None, region="Punjab"):
#     """Fetches Urdu news based on the region."""
#     all_news = []
#
#     # If no region is specified, use a broader approach
#     if region.lower() == "unknown" or not region:
#         region = "پاکستان"  # Default to "Pakistan" for general news
#
#     for feed_url in URDU_NEWS_FEEDS:
#         feed = feedparser.parse(feed_url)
#         for entry in feed.entries[:5]:  # Fetch top 5 news per source
#             title = entry.get("title", "No title available")
#             link = entry.get("link", "#")
#
#             # Check if region (or keyword) is in the title or description
#             if region.lower() in title.lower() or region.lower() in entry.get("summary", "").lower():
#                 all_news.append({"title": title, "link": link})
#
#     return "\n\n".join(format_news(all_news, language="ur")) if all_news else "کوئی خبر دستیاب نہیں"

def fetch_english_news(topic=None):
    """
    Fetches English news headlines from RSS feeds with optional topic filtering.
    :param topic: (Optional) Fetch only news related to a specific topic (e.g., "sports").
    :return: Formatted English news headlines.
    """
    all_news = []

    for feed_url in ENGLISH_NEWS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Fetch top 5 news per source
            title = entry.get("title", "No title available")
            link = entry.get("link", "#")

            # If a topic is provided, filter news based on the topic keyword
            if topic and topic.lower() not in title.lower():
                continue

            all_news.append({"title": title, "link": link})

    if all_news:
        formatted_news = "\n\n".join(format_news(all_news, language="en"))
        return f"<strong>Latest News:</strong>\n\n{formatted_news}"  # Heading in English
    return "Sorry! No news available."


def fetch_news(language="ur", topic=None):
    """Fetches news based on user's language and region preference."""
    user_region = current_user.region if current_user.is_authenticated else "Punjab"
    print(user_region)

    if language == "en":
        return fetch_english_news(topic)
    return fetch_urdu_news(topic)


def fetch_events(city="Lahore"):
    """
    Scrapes events from Allevents.in for the specified city.
    :param city: The city for which events are fetched.
    :return: List of event details with subtitle and date.
    """
    events = []

    # Scrape Allevents.in
    allevents_url = f"https://allevents.in/{city.lower()}"
    response = requests.get(allevents_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all event divs with the class 'meta'
        event_divs = soup.find_all("div", class_="meta", limit=10)

        for event in event_divs:
            # Extract event title and link
            title_tag = event.find("a", href=True)
            subtitle_tag = event.find("div", class_="subtitle")
            date_tag = event.find("div", class_="date")

            if title_tag and subtitle_tag and date_tag:
                title = title_tag.get_text(strip=True)
                subtitle = subtitle_tag.get_text(strip=True)
                date = date_tag.get_text(strip=True)
                url = title_tag["href"]

                # Format the event details
                events.append(f"🔹 <strong>{title}</strong>\n"
                              f"   <em>{subtitle}</em>\n"
                              f"   <strong>Date:</strong> {date}\n"
                              f"   <a href='{url}' target='_blank'>Details</a>\n")

    return events if events else ["No events found in your area."]

# Run test
print(fetch_events("Lahore"))
