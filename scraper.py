import pandas as pd
import time
import random
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from urllib.parse import quote
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def get_job_info(job_card):
    """Extracts job information from a single job card."""
    base_url = "https://www.indeed.com"
    job_data = {
        'title': "N/A", 
        'company': "N/A", 
        'location': "N/A", 
        'link': "N/A",
        'date_posted': "N/A"
    }
    
    try:
        # Extract job title and link
        title_element = job_card.find('h2', class_='jobTitle')
        if title_element:
            link_element = title_element.find('a')
            if link_element and link_element.has_attr('href'):
                job_data['title'] = link_element.text.strip()
                job_data['link'] = base_url + link_element['href']
    except Exception as e:
        logging.warning(f"Error extracting title/link: {e}")
    
    try:
        # Extract company name
        company_elements = job_card.find_all('span', {'data-testid': 'company-name'})
        if company_elements:
            job_data['company'] = company_elements[0].text.strip()
    except Exception as e:
        logging.warning(f"Error extracting company: {e}")
    
    try:
        # Extract location
        location_elements = job_card.find_all('div', {'data-testid': 'text-location'})
        if location_elements:
            job_data['location'] = location_elements[0].text.strip()
    except Exception as e:
        logging.warning(f"Error extracting location: {e}")
    
    try:
        # Extract date posted
        date_elements = job_card.find_all('span', {'data-testid': 'myJobsStateDate'})
        if date_elements:
            job_data['date_posted'] = date_elements[0].text.strip()
    except Exception as e:
        logging.warning(f"Error extracting date: {e}")
        
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
            (By.XPATH, "//div[contains(@class, 'description')]"),
            (By.TAG_NAME, "body")
        ]
        
        for by, selector in selectors:
            try:
                wait = WebDriverWait(driver, 15)
                desc_element = wait.until(EC.presence_of_element_located((by, selector)))
                description = desc_element.text.strip()
                if description and len(description) > 50:  # Basic validation
                    return description
            except Exception:
                continue
                
        return "Description not found."
    except Exception as e:
        logging.error(f"Error extracting description from {job_link}: {e}")
        return "Error loading description"

def setup_driver(headless=True):
    """Set up and configure the Chrome driver."""
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Apply stealth settings
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

def main():
    """Main function to scrape job data."""
    search_query = "data scientist"
    location = "New York, NY"
    max_pages = 3
    all_jobs = []
    
    # Detect if running in GitHub Actions (headless environment)
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    logging.info("Starting job scraper...")
    logging.info(f"Search: {search_query}, Location: {location}")
    
    driver = setup_driver(headless=is_github_actions)
    
    try:
        for page in range(max_pages):
            start = page * 10
            encoded_query = quote(search_query)
            encoded_location = quote(location)
            url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_location}&start={start}"
            
            logging.info(f"Scraping page {page + 1}: {url}")
            
            driver.get(url)
            
            # Wait for job cards to load
            try:
                WebDriverWait(driver, 25 if is_github_actions else 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon"))
                )
                logging.info("Job cards loaded successfully")
            except Exception as e:
                logging.error(f"Timeout waiting for job cards: {e}")
                break
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'lxml')
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            logging.info(f"Found {len(job_cards)} job cards on page {page + 1}")
            
            if not job_cards:
                logging.warning("No job cards found. Stopping.")
                break
            
            for i, card in enumerate(job_cards):
                job_data = get_job_info(card)
                
                if job_data['link'] != "N/A":
                    logging.info(f"Processing job {i + 1}: {job_data['title']}")
                    job_data['description'] = extract_description(driver, job_data['link'])
                else:
                    job_data['description'] = "N/A"
                    logging.warning(f"Job {i + 1} has no link, skipping description extraction")
                
                all_jobs.append(job_data)
                
                # Add delay between job processing
                delay = random.uniform(2, 5) if is_github_actions else random.uniform(1, 3)
                logging.info(f"Waiting {delay:.2f} seconds before next job...")
                time.sleep(delay)
            
            # Add delay between pages
            if page < max_pages - 1:
                page_delay = random.uniform(3, 7)
                logging.info(f"Waiting {page_delay:.2f} seconds before next page...")
                time.sleep(page_delay)
    
    except Exception as e:
        logging.error(f"Unexpected error during scraping: {e}")
    finally:
        logging.info("Closing browser...")
        driver.quit()
    
    # Save results
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        output_file = 'raw_job_data.csv'
        df.to_csv(output_file, index=False)
        
        logging.info(f"Scraping complete! Saved {len(df)} jobs to {output_file}")
        
        # Summary statistics
        valid_links = len(df[df['link'] != 'N/A'])
        valid_descriptions = len(df[~df['description'].isin(['N/A', 'Description not found.', 'Error loading description'])])
        
        logging.info(f"Jobs with valid links: {valid_links}/{len(df)}")
        logging.info(f"Jobs with descriptions: {valid_descriptions}/{len(df)}")
    else:
        logging.warning("No jobs were scraped.")

if __name__ == "__main__":
    import os
    main()