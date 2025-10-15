import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class TestReview:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.driver = webdriver.Edge()
        self.driver.maximize_window()
        yield
        self.driver.quit()
    
    def test_20251003Review(self):
      
      # Open the website
      self.driver.get("https://kinerja.jabarprov.go.id/")
      
      # PAUSE HERE - Log in manually!
      print("\n=== PLEASE LOG IN MANUALLY ===")
      print("You have 60 seconds to log in...")
      time.sleep(60)  # Wait 60 seconds for you to log in
      print("Continuing with automation...\n")
      
      # Automation starts here
      max_iterations = 15  # Safety limit
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