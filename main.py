import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from flask import Flask, render_template

app = Flask(__name__)

TARGET_URL = "https://www.wired.com"

START_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
# START_DATE = datetime(2023, 12, 12, tzinfo=timezone.utc)

def getDate(link):
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        date_element = soup.find('time', attrs={'data-testid': "ContentHeaderPublishDate"})

        if date_element and 'datetime' in date_element.attrs:

            date_str = date_element['datetime']

            try:
                article_datetime = datetime.fromisoformat(date_str)

                if article_datetime.tzinfo is None or article_datetime.tzinfo.utcoffset(article_datetime) is None:
                    article_datetime = article_datetime.replace(tzinfo=timezone.utc)
                
                return article_datetime.astimezone(timezone.utc)
            
            except ValueError as e:
                print(f"Error parsing date string '{date_str}' for {link}: {e}")
                return None
        else:
            print(f"Date element not found for: {link}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching date from {link}: {e}")
        return None
    except Exception as e:
        print(f"Error gettin date from {link}: {e}")
        return None

def scrape_wired():
    articles_data = []
    try:
        response = requests.get(TARGET_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        latest_articles = soup.find_all('div', class_='summary-item')
        print(f"Found {len(latest_articles)} articles.")

        for article in latest_articles:
            title_element = article.find('h2') or article.find('h3')#attrs={'data-testid': "SummaryItemHed"}
            link_element = article.find('a', class_='SummaryItemImageLink-dshqxb')

            title = None
            link = None

            if title_element:
                title = title_element.get_text(strip=True)
            else:
                print(f"Warning: Title not found for an article.")
                continue

            if link_element and 'href' in link_element.attrs:
                href = link_element['href']
                if href.startswith(TARGET_URL):
                    link = href
                else:
                    link = TARGET_URL + href

            else:
                print(f"Warning: Link not found for {title}")

            if title and link:
                article_datetime_utc = getDate(link)
                # print(f"Article: {title}, Link: {link}, Date (UTC): {article_datetime_utc}")

                #ignore older articles
                if article_datetime_utc and article_datetime_utc >= START_DATE:
                    articles_data.append({'title': title, 'link': link, 'date': article_datetime_utc})

                else:
                    print("Could not get date for: {title}")
            else:
                print("Warning: Skipping article due to missing title or link.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
    except Exception as e:
        print(f"Scraping error: {e}")

    articles_data.sort(key=lambda x: x['date'], reverse=True)
    return articles_data

@app.route('/')
def index():
    articles = scrape_wired()
    return render_template('index.html', articles=articles)

if __name__ == '__main__':
    app.run(debug=True)