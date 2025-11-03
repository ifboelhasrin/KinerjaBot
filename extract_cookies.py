#!/usr/bin/env python3
"""
Helper script to extract cookies by automated login.
Enter username and password in terminal, script will automate login.
"""

import pickle
import time
import os
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def extract_cookies():
    """Automate login and extract cookies"""
    print("\n" + "="*60)
    print("=== SAFARI COOKIE EXTRACTION (Automated Login) ===")
    print("="*60)
    print("\n📋 This script will:")
    print("   1. Ask for your username and password in terminal")
    print("   2. Open Safari and automate the login process")
    print("   3. Extract and save cookies for future use")
    print("\n" + "="*60)
    
    # Get credentials from terminal
    print("\n🔐 Enter your login credentials:")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()
    
    if not username or not password:
        print("\n❌ Username and password are required!")
        return False
    
    driver = None
    try:
        print("\n🔧 Opening Safari...")
        driver = webdriver.Safari()
        driver.maximize_window()
        
        print("🌐 Navigating to login page...")
        driver.get("https://kinerja.jabarprov.go.id/")
        
        # Wait a bit for page to load
        time.sleep(3)
        
        print("🔍 Looking for login form...")
        
        # Try to find username/email field (common selectors)
        username_field = None
        username_selectors = [
            (By.ID, "username"),
            (By.ID, "email"),
            (By.ID, "user"),
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name*='user']"),
            (By.CSS_SELECTOR, "input[name*='email']"),
            (By.XPATH, "//input[@placeholder='Username' or @placeholder='Email']"),
        ]
        
        for selector_type, selector_value in username_selectors:
            try:
                username_field = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                print(f"✓ Found username field using {selector_type}={selector_value}")
                break
            except TimeoutException:
                continue
        
        if not username_field:
            print("\n⚠️  Could not find username field automatically.")
            print("💡 Please inspect the login page and update the selectors in extract_cookies.py")
            return False
        
        # Try to find password field
        password_field = None
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        
        for selector_type, selector_value in password_selectors:
            try:
                password_field = driver.find_element(selector_type, selector_value)
                print(f"✓ Found password field using {selector_type}={selector_value}")
                break
            except NoSuchElementException:
                continue
        
        if not password_field:
            print("\n⚠️  Could not find password field automatically.")
            return False
        
        # Fill in credentials
        print("\n✍️  Entering credentials...")
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)
        
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)
        
        # Try to find and click submit button
        submit_button = None
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Masuk') or contains(text(), 'Sign')]"),
            (By.XPATH, "//input[@value='Login' or @value='Masuk' or @value='Sign In']"),
            (By.CSS_SELECTOR, ".btn-primary"),
            (By.CSS_SELECTOR, ".button-login"),
        ]
        
        for selector_type, selector_value in submit_selectors:
            try:
                submit_button = driver.find_element(selector_type, selector_value)
                print(f"✓ Found submit button using {selector_type}={selector_value}")
                break
            except NoSuchElementException:
                continue
        
        if submit_button:
            print("🔘 Clicking submit button...")
            submit_button.click()
        else:
            print("⚠️  Could not find submit button, trying to submit form...")
            password_field.submit()
        
        # Wait for login to complete
        print("⏳ Waiting for login to complete...")
        time.sleep(5)
        
        # Check if login was successful by checking URL
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        # Extract cookies
        print("\n🔍 Extracting cookies...")
        cookies = driver.get_cookies()
        
        if cookies:
            cookie_file = "cookies.pkl"
            pickle.dump(cookies, open(cookie_file, "wb"))
            print(f"\n✅ SUCCESS!")
            print(f"   Extracted {len(cookies)} cookies")
            print(f"   Saved to: {cookie_file}")
            print("\n🎉 Cookies saved! You can now run your automation script:")
            print("   python3 -m pytest '20251003 TESTED autoReview.py' -v -s")
            print("   It will automatically use these cookies and skip login.")
            
            # Keep browser open for a moment so user can verify login
            print("\n⏱️  Keeping browser open for 5 seconds so you can verify login...")
            time.sleep(5)
            
            return True
        else:
            print("\n⚠️  No cookies found!")
            print("\n💡 TROUBLESHOOTING:")
            print("   - Login might have failed - check the Safari window")
            print("   - Make sure credentials are correct")
            print("   - Website might have changed login form structure")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 TROUBLESHOOTING:")
        print("   - Check if Safari WebDriver is properly set up")
        print("   - Make sure the website is accessible")
        print("   - Verify your credentials are correct")
        return False
        
    finally:
        if driver:
            print("\n🔒 Closing Safari...")
            driver.quit()

if __name__ == "__main__":
    success = extract_cookies()
    if not success:
        print("\n" + "="*60)
        print("Login failed. Please check:")
        print("  1. Your username and password are correct")
        print("  2. The website login form hasn't changed")
        print("  3. You have internet connection")
        print("="*60)
