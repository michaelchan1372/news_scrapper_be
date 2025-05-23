import os
import tempfile
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from pywebcopy import save_webpage
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

import services.database as database
import services.file_write as file_write

selectors = [
            "article",               # Most semantic tag
            "main",                  # Usually used for main page content
            "section",               # Sometimes used in place of article
            "div.article-content",   # Common pattern (update based on site)
            "div.post-content",      # Another common pattern
            "div.entry-content",     # Used in WordPress and blogs
            "div.content",           # Generic fallback
        ]

def init_driver():
    print("init chrome driver")
    options = Options()
    options.add_argument("--headless")  # Optional: run without opening a window
    # Create a unique temporary directory
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    driver = webdriver.Remote(
    command_executor='http://selenium:4444/wd/hub',
    options=options
    )
    return driver
    #return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_article(driver, news_item, conn, region_name, keyword):
    news_link = news_item["link"]
    id = news_item["id"]
    try:
        driver.get(news_link)
        sleep(5)  # Wait for the page to load
        
        
        # Approach 1, soup
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        content = soup.get_text(separator="\n", strip=True)
        content = re.sub(r'\n{2,}', '\n', content)
        
        # Approach 2, use different tags, filtered by keywords
        
        texts = soup.find_all(string=True)
        visible_texts = [t.strip() for t in texts if is_visible_text(t) and t.strip()]
        filtered_lines = [line for line in visible_texts if contains_keyword(line, [keyword])]
        content = "\n".join(visible_texts)
        content_filtered = "\n".join(filtered_lines)
        
        content_path =  f"./output/{region_name}/content/" + str(news_item["id"]) + ".txt"
        content_filtered_path = f"./output/{region_name}/content/" + str(news_item["id"]) + "_filtered.txt"
        html_path =  f"./output/{region_name}/content/" + str(news_item["id"])
        saveToCsv(content, content_path, region_name)
        saveToCsv(content_filtered, content_filtered_path, region_name)
        #archieveSite(driver, html_path, news_link)
        udpateDbPath(conn, id, content_path, html_path)
        # Todo: Save as a html file
        return (content)
    except Exception as e:
        print(f"Error scraping {news_link}: {e}")
        return ""

def saveToCsv(content, content_path, region_name):
    file_write.create_folder_if_not_exist(f"./output/{region_name}/content")
    file_write.write_to_text(content, content_path)
 
def archieveSite(driver, html_path, news_link):
    try:
        file_write.create_folder_if_not_exist(html_path)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all(['img', 'script', 'link'])
        for tag in tags:
            attr = 'src' if tag.name in ['img', 'script'] else 'href'
            if tag.has_attr(attr):
                file_url = urljoin(news_link, tag[attr])
                local_name = download_file(file_url, html_path)
                if local_name:
                    tag[attr] = local_name
        with open(os.path.join(html_path, "index.html"), "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        file_write.zip_folder(html_path, html_path + ".zip")
    except Exception as e:
        
        print("Failed to scrape" + driver.current_url)
        print(e)

def udpateDbPath(conn, id, content_path, html_path):
    database.save_path(conn, id, content_path, html_path)
    conn.commit()

def download_file(url, folder):
    
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(folder, filename)
    if not url or not filename:
        return None
    try:
        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return filename
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def is_visible_text(element):
    """Helper to filter out invisible/scripting elements."""
    from bs4.element import Comment
    return (
        not isinstance(element, Comment) and
        element.parent.name not in ["style", "script", "head", "meta", "[document]"]
    )

def contains_keyword(text, keywords):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)