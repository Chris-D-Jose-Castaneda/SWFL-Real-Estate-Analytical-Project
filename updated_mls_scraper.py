# Hi, This is the final version of the MLS scraper. I made some changes to the original file to make it more readable and efficient.
# Source: https://www.realtyofnaples.com/
# This is the Data Collection Step. This is technically the first major step of the project 

# Import libraries
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException, 
    NoSuchElementException, 
    TimeoutException, 
    WebDriverException
)

# Set up Firefox options
firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--no-sandbox")
firefox_options.add_argument("--disable-dev-shm-usage")

# Function to initialize WebDriver
def init_driver():
    # NOTE: Provide correct raw string or double backslashes in path

    # YOU HAVE TO DOWNLOAD GECKODRIVER AND PUT IT IN THE PATH // This is my path 
    # Source: https://github.com/mozilla/geckodriver/releases
    driver_service = Service(r"C:\Users\chris\Downloads\geckodriver-v0.36.0-win64\geckodriver.exe")       
    driver = webdriver.Firefox(service=driver_service, options=firefox_options)
    return driver

driver = init_driver()

# Def function to open the website 
def open_main_url(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.commlst.clearfix'))
        )
    except TimeoutException:
        print("Timeout: Page did not load within 30 seconds.")
        driver.quit()

# I updated the URL to https://www.realtyofnaples.com/ [Naples, Bonita Springs, Estero, etc]
url = 'https://www.realtyofnaples.com/Bonita-Springs'
open_main_url(driver, url)



# Create a list to store the scraped data
data = []

# Function to scroll down to the bottom of the page
def scroll_down():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Adjust the sleep time if necessary

# Function to save data periodically
def save_data():
    df = pd.DataFrame(data)
    df.to_csv('april13_listings.csv', index=False)
    print("Data saved to april13_listings.csv")

# Function to save the state
def save_state(last_processed_index):
    with open('last_state.txt', 'w') as file:
        file.write(str(last_processed_index))
    print("State saved.")

# Function to load the last saved state
def load_state():
    if os.path.exists('last_state.txt'):
        with open('last_state.txt', 'r') as file:
            return int(file.read().strip())
    return 0

# Function to scrape the details of a single listing
def scrape_listing(listing_url):
    try:
        driver.get(listing_url)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.info_div'))
        )
        
        # Scroll down to load all information
        scroll_down()

        price = driver.find_element(By.CSS_SELECTOR, 'div.price_div').text
        address = driver.find_element(By.CSS_SELECTOR, 'a[itemprop="name"]').text
        details = driver.find_element(By.CSS_SELECTOR, 'div.info_div').text
        try:
            description = driver.find_element(By.CSS_SELECTOR, 'p.txtblk').text
        except NoSuchElementException:
            description = "No description available"

        # Scrape the table details
        features = driver.find_elements(By.CSS_SELECTOR, 'div.features_column')
        features_text = [feature.text for feature in features]

        # Extract Beds, Baths, Sqft from details text
        beds = baths = sqft = 0
        try:
            beds = int(details.split('Beds')[0].split()[-1])
        except:
            pass
        try:
            baths = int(details.split('Baths')[0].split()[-1])
        except:
            pass
        try:
            sqft = int(details.split('ft²')[0].split()[-1].replace(',', ''))
        except:
            pass

        # Extract additional information
        additional_info = "\n".join([feature.text for feature in features])
        
        # Extract agent information
        try:
            agent_info = driver.find_element(By.ID, 'agent_name').text
        except NoSuchElementException:
            agent_info = "No agent information available"

        data.append({
            'price': price,
            'address': address,
            'beds': beds,
            'baths': baths,
            'sqft': sqft,
            'link': listing_url,
            'description': description,
            'features': features_text,
            'additional_info': additional_info,
            'agent_info': agent_info
        })

        print(price, address, beds, baths, sqft, description, features_text, additional_info, agent_info)
    except Exception as e:
        print(f"Error scraping listing: {e}")

# Function to scrape a single community
def scrape_community(community_url):
    try:
        driver.get(community_url)
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.result_box'))
        )
        
        listings = driver.find_elements(By.CSS_SELECTOR, 'a.view_details_url')
        print(f"Found {len(listings)} listings in the community.")
        for i in range(len(listings)):
            try:
                listing = driver.find_elements(By.CSS_SELECTOR, 'a.view_details_url')[i]
                listing_url = listing.get_attribute('href')
                scrape_listing(listing_url)
                driver.back()
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.result_box'))
                )
            except StaleElementReferenceException:
                print("Stale element, continuing.")
                continue
            except Exception as e:
                print(f"Error processing listing: {e}")
                continue
    except Exception as e:
        print(f"Error scraping community page: {e}")

# Main function to scrape all communities
def scrape_communities():
    global driver
    community_links = driver.find_elements(By.CSS_SELECTOR, 'div.commlst.clearfix a')
    print(f"Found {len(community_links)} community links.")
    start_index = load_state()
    for link_index, link in enumerate(community_links[start_index:], start=start_index):
        try:
            community_url = link.get_attribute('href')
            scrape_community(community_url)
            driver.back()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.commlst.clearfix'))
            )
            if link_index % 5 == 0:  # Save data and state every 5 communities
                save_data()
                save_state(link_index)
        except StaleElementReferenceException:
            print("Stale element in main community list, continuing.")
            continue
        except WebDriverException as e:
            print(f"WebDriverException: {e}. Retrying...")
            driver.quit()
            time.sleep(10)
            driver = init_driver()
            open_main_url(driver, url)
            scrape_community(community_url)
        except Exception as e:
            print(f"Error processing community link: {e}")
            continue

# Start scraping
scrape_communities()

# Close the driver
driver.quit()

# Save final data and state
save_data()
save_state(len(driver.find_elements(By.CSS_SELECTOR, 'div.commlst.clearfix a')))

# Again the original file looks so goofy so I did some changes with excel formulas. I'll share the raw data and then the latest version. 
# Any other future saved files will be deleted on the zip folder
print("Scraping completed. Data saved to april13_listings.csv")
