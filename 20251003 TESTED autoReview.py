import pytest
import time
import pickle
import os
from getpass import getpass
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
    
    def load_cookies(self, url=None):
        """Load saved cookies if they exist"""
        # Try multiple cookie files (same pattern as autoKuesioner)
        cookie_files = ["peer_review_cookies.pkl", "cookies.pkl"]
        
        for cookie_file in cookie_files:
            if os.path.exists(cookie_file):
                try:
                    # Navigate to a page first (required for adding cookies)
                    if url:
                        self.driver.get(url)
                    else:
                        self.driver.get("https://kinerja.jabarprov.go.id/")
                    
                    # Load cookies from file
                    cookies = pickle.load(open(cookie_file, "rb"))
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            print(f"Could not add cookie: {e}")
                    self.driver.refresh()
                    print(f"✓ Loaded cookies from {cookie_file}")
                    return True
                except Exception as e:
                    print(f"Error loading cookies from {cookie_file}: {e}")
                    continue
        
        return False
    
    def save_cookies(self):
        """Save cookies for future use"""
        try:
            cookie_file = "cookies.pkl"
            pickle.dump(self.driver.get_cookies(), open(cookie_file, "wb"))
            print("✓ Cookies saved successfully!")
        except Exception as e:
            print(f"Could not save cookies: {e}")
    
    def login_via_terminal(self):
        """Prompt for credentials in terminal and automate login"""
        print("\n" + "="*60)
        print("🔐 LOGIN REQUIRED")
        print("="*60)
        print("\n📋 Please enter your login credentials:")
        username = input("Username: ").strip()
        password = getpass("Password: ").strip()
        
        if not username or not password:
            print("\n❌ Username and password are required!")
            return False
        
        try:
            print("\n🌐 Navigating to login page...")
            self.driver.get("https://kinerja.jabarprov.go.id/")
            time.sleep(3)
            
            # Find username field
            username_field = None
            username_selectors = [
                (By.ID, "username"),
                (By.ID, "email"),
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[type='email']"),
            ]
            
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"✓ Found username field")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                print("⚠️  Could not find username field automatically.")
                return False
            
            # Find password field
            password_field = None
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    print(f"✓ Found password field")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                print("⚠️  Could not find password field automatically.")
                return False
            
            # Fill credentials
            print("✍️  Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # Find and click submit button
            submit_button = None
            submit_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Masuk')]"),
                (By.CSS_SELECTOR, ".btn-primary"),
            ]
            
            for selector_type, selector_value in submit_selectors:
                try:
                    submit_button = self.driver.find_element(selector_type, selector_value)
                    print(f"✓ Found submit button")
                    break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                print("🔘 Clicking submit button...")
                submit_button.click()
            else:
                print("⚠️  Could not find submit button, trying form submit...")
                password_field.submit()
            
            # Wait for login to complete
            print("⏳ Waiting for login to complete...")
            time.sleep(5)
            
            print("✓ Login completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False
    
    def test_20251003Review(self):
      
      # Try to load saved cookies first
      cookies_loaded = self.load_cookies()
      
      if not cookies_loaded:
          print("\n" + "="*60)
          print("ℹ️  No cookies found or cookies invalid.")
          print("🔐 Starting automated login via terminal...")
          print("="*60)
          
          # Login via terminal input
          login_success = self.login_via_terminal()
          
          if not login_success:
              raise Exception("Login failed. Please check your credentials and try again.")
          
          # Save cookies for next time
          print("\n💾 Saving cookies for future use...")
          self.save_cookies()
          time.sleep(2)
      else:
          print("✓ Loaded saved cookies - skipping manual login")
          time.sleep(2)  # Brief pause to ensure page is loaded
      
      # Automation starts here
      max_iterations = 100  # Safety limit
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