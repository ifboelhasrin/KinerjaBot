import pytest
import time
import pickle
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class TestReview:
    @pytest.fixture(autouse=True)
    # SAFARI BROWSER
    def setup(self):
        self.driver = webdriver.Safari()
        self.driver.maximize_window()
        yield
        self.driver.quit()
    
    def load_cookies(self):
        """Load saved cookies if they exist"""
        cookie_file = "cookies.pkl"
        if os.path.exists(cookie_file):
            try:
                self.driver.get("https://kinerja.jabarprov.go.id/")
                cookies = pickle.load(open(cookie_file, "rb"))
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Could not add cookie: {e}")
                self.driver.refresh()
                return True
            except Exception as e:
                print(f"Error loading cookies: {e}")
        return False
    
    def save_cookies(self):
        """Save cookies for future use"""
        try:
            cookie_file = "cookies.pkl"
            pickle.dump(self.driver.get_cookies(), open(cookie_file, "wb"))
            print("✓ Cookies saved successfully!")
        except Exception as e:
            print(f"Could not save cookies: {e}")
    
    def test_20251003Review(self):
      
      # Try to load saved cookies first
      cookies_loaded = self.load_cookies()
      
      if not cookies_loaded:
          
          print("❌ No cookies found - please extract cookies first using 'python3 extract_cookies.py'")
          raise Exception("No cookies found. Please extract cookies from regular Safari first using 'python3 extract_cookies.py'")
          
      else:
          print("✓ Loaded saved cookies - skipping manual login")
          time.sleep(2)  # Brief pause to ensure page is loaded
      
      # Automation starts here
      max_iterations = 25  # Safety limit
      iteration = 0
      
      while iteration < max_iterations:
          self.driver.get("https://kinerja.jabarprov.go.id/kinerjajabar/review-perilaku")
          
          try:
              # Wait for page to load and check if "Lakukan Review" link exists
              review_button = WebDriverWait(self.driver, 10).until(
                  EC.presence_of_element_located((By.LINK_TEXT, "Lakukan Review"))
              )
              
              # Click the review button
              review_button.click()
              
              # Click all 7 rating elements
              for i in range(1, 8):
                  selector = f".flex:nth-child({i}) > .flex > .flex > .hidden > .bg-white:nth-child(6)"
                  element = WebDriverWait(self.driver, 10).until(
                      EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                  )
                  element.click()
              
              # Click submit button
              submit_button = WebDriverWait(self.driver, 10).until(
                  EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-green > span"))
              )
              submit_button.click()
              
              iteration += 1
              
          except (NoSuchElementException, TimeoutException):
              # If "Lakukan Review" button not found, exit loop
              break