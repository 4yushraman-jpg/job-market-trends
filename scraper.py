import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from urllib.parse import quote
import re

def get_job_info(job_card):
    """Extracts job information from a single job card."""
    base_url = "https://www.indeed.com"
    job_data = {'title': "N/A", 'company': "N/A", 'location': "N/A", 'link': "N/A"}
    
    try:
        title_element = job_card.find('h2', class_='jobTitle').find('a')
        job_data['title'] = title_element.text.strip()
        job_data['link'] = base_url + title_element['href']
    except (AttributeError, TypeError):
        pass
        
    try:
        company_name = job_card.find('span', {'data-testid': 'company-name'})
        if company_name:
            job_data['company'] = company_name.text.strip()
    except (AttributeError, TypeError):
        pass
        
    try:
        company_location = job_card.find('div', {'data-testid': 'text-location'})
        if company_location:
            job_data['location'] = company_location.text.strip()
    except (AttributeError, TypeError):
        pass
        
    return job_data

def extract_description(driver, job_link):
    """Extracts job description from a job detail page."""
    if job_link == "N/A":
        return "N/A"
        
    try:
        driver.get(job_link)
        
        # Try multiple selectors for job description
        selectors = [
            (By.ID, "jobDescriptionText"),
            (By.CLASS_NAME, "jobsearch-jobDescriptionText"),
            (By.CLASS_NAME, "job-description"),
            (By.XPATH, "//div[contains(@class, 'description')]")
        ]
        
        for by, selector in selectors:
            try:
                wait = WebDriverWait(driver, 10)
                desc_element = wait.until(EC.presence_of_element_located((by, selector)))
                return desc_element.text.strip()
            except Exception:
                continue
                
        return "Description not found."
    except Exception as e:
        print(f"Error extracting description: {e}")
        return "Error loading description"

def main():
    """Main function to scrape job data using selenium-stealth and human-like delays."""
    search_query = "data scientist"
    location = "New York, NY"
    all_jobs = []

    print("Starting stealth Selenium browser...")
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    try:
        # Scrape 3 pages for a good sample size
        for start in range(0, 30, 10): 
            # Proper URL encoding
            encoded_query = quote(search_query)
            encoded_location = quote(location)
            url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_location}&start={start}"
            
            print(f"\nScraping search results page {start//10 + 1}...")
            
            driver.get(url)
            
            print("  -> Waiting for job cards to load...")
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "job_seen_beacon"))
                )
                print("  -> Job cards found.")
            except Exception as e:
                print(f"  -> Error waiting for job cards: {e}. Stopping.")
                break

            soup = BeautifulSoup(driver.page_source, 'lxml')
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            print(f"  -> Found {len(job_cards)} jobs on this page.")

            for card in job_cards:
                job_data = get_job_info(card)
                
                if job_data['link'] != "N/A":
                    print(f"  -> Getting description for: {job_data['title']}")
                    job_data['description'] = extract_description(driver, job_data['link'])
                else:
                    job_data['description'] = "N/A"
                
                all_jobs.append(job_data)

                # Add a longer, random delay to mimic human behavior
                sleep_time = random.uniform(3, 8)
                print(f"    ... waiting for {sleep_time:.2f} seconds ...")
                time.sleep(sleep_time)
    
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        print("\nClosing Selenium browser...")
        driver.quit()

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        print("\n--- Scraping Complete ---")
        print(f"Total jobs scraped: {len(df)}")
        df.to_csv('raw_job_data.csv', index=False)
        print("\nSuccessfully saved raw job data to raw_job_data.csv")
        
        # Basic data validation
        print(f"Jobs with valid links: {len(df[df['link'] != 'N/A'])}")
        print(f"Jobs with descriptions: {len(df[df['description'].str.contains('not found|N/A|Error') == False])}")
    else:
        print("No jobs were scraped.")

if __name__ == "__main__":
    main()