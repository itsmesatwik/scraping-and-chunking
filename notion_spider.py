import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import openai

openai.api_key = "API_KEY_HERE"
MODEL = "gpt-3.5-turbo"


def callOpenAI(message):
    prompt = f"""
Assume the role of a critical high accuracy text parser.
Your task is to break down the following string into chunks of about 750 words.
- You MUST keep headers and paragrahs together.
- You MUST keep the bulleted lists together and not break them up mid-list.
- You may go above 750 words to keep related context together.
- Your final output should be an array of these chunks.
- You MUST return an array of chunks, any other format of response will be penalized.
Here is the string:
{message}
"""
    chat_completion = openai.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}]
    )
    response_message = chat_completion.choices[0].message.content
    print(response_message)
    return response_message

def articleChunks(articles):
    ret = []
    for article in articles:
        print(article["title"])
        message = article["body"]
        response = callOpenAI(message)
        response_cleaned = response.replace('\n', '')
        chunks = json.loads(response_cleaned, strict=False)
        chunk_data = {
            "url": article['url'],
            "title": article['title'],
            "chunks": chunks,
        }
        ret.append(chunk_data)
    if not os.path.exists('output/chunks'):
        os.makedirs('output/chunks')
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'output/chunks/notion_help_articles_chunks_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(ret, f, indent=4)



class NotionScraper:
    def __init__(self):
        self.start_url = "https://www.notion.so/help"
        self.base_url = "https://www.notion.so"
        self.output_dir = 'output'
        self.scraped_data = []

    def fetch_page(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve {url}")
            return None
    
    def parse_article2(self, url):
        page_content = self.fetch_page(url)
        if page_content:
            soup = BeautifulSoup(page_content, 'html.parser')

            # Extract the title
            title = soup.find('h1').get_text() if soup.find('h1') else "No title"

            # Extract all text content within the section tag with the given class
            section_tag = soup.select_one('section.helpCenterContentSpacing_contentSpacing__7jwfD')
            body = section_tag.get_text(separator='\n', strip=True) if section_tag else "No content"

            # Save article data
            article_data = {
                'url': url,
                'title': title,
                'body': body,
            }
            self.scraped_data.append(article_data)


    def find_links(self, soup):
        link_pattern = re.compile(r'/help/[-a-zA-Z0-9]+$')
        return [self.base_url + a['href'] for a in soup.find_all('a', href=True, class_='toggleList_link__safdF') if link_pattern.match(a['href'])]

    def scrape(self):
        # Fetch main help page
        main_page_content = self.fetch_page(self.start_url)
        if main_page_content:
            soup = BeautifulSoup(main_page_content, 'html.parser')
            article_links = self.find_links(soup)
            links = set(article_links)

            # Loop through each article link and scrape the article content
            for link in links:
                self.parse_article2(link)

    def save_data(self):
        # Create the output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f'{self.output_dir}/notion_help_articles_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(self.scraped_data, f, indent=4)

        print(f"Data saved to {filename}")
    
    def chunking(self):
        articleChunks(self.scraped_data)


if __name__ == "__main__":
    # data = None
    # with open('output/notion_help_articles_2024-10-13_03-00-19.json', 'r') as file:
    #     data = json.load(file)
    # articleChunks(data)
    scraper = NotionScraper()
    scraper.scrape()
    scraper.save_data()
    scraper.chunking()
