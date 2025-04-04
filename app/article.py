import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json
import re

class Article:
    def scrap_articles() : 
        today = datetime.today()
        today_str = today.strftime("%d/%m/%Y")
        from_date = (today - timedelta(days=7)).strftime("%d/%m/%Y")

        print(today_str.replace, from_date)

        # Base URL
        base_url = f"https://www.detik.com/search/searchnews?query=harga%20bahan%20pangan&result_type=latest&fromdatex={from_date}&todatex={today_str}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        num_pages = 5
        data = []

        for page in range(1, num_pages + 1):
            # print(f"Scraping page {page}...")
            url = base_url + f"&page={page}"

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Failed to fetch page {page}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            news_list = soup.find_all("article")

            for news in news_list:
                try:
                    title = news.find("h3").text.strip()
                    link = news.find("a")["href"]
                    desc = news.find("div", class_="media__desc").text.strip()
                    date = news.find("div", class_="media__date").text.strip()

                    image_tag = news.find("div", class_="media__image").find("img")
                    image_url = image_tag["src"] if image_tag else None


                    data.append({
                        "title": title,
                        "link": link,
                        "description": desc,
                        "date": date,
                        "img_url": image_url
                    })
                except AttributeError:
                    continue

            time.sleep(0.5)

        # Output as JSON
        return data