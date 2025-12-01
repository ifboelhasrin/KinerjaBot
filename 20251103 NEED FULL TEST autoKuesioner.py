import pytest
import time
import pickle
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class TestKuesioner:
    @pytest.fixture(autouse=True)
    # SAFARI BROWSER
    def setup(self):
        self.driver = webdriver.Safari()
        self.driver.maximize_window()
        yield
        self.driver.quit()
    
    def load_cookies(self, url=None):
        """Load peer-review cookies if they exist"""
        # Try peer-review cookies first, fallback to regular cookies
        cookie_files = ["peer_review_cookies.pkl", "cookies.pkl"]
        
        for cookie_file in cookie_files:
            if os.path.exists(cookie_file):
                try:
                    # Navigate to a page first (required for adding cookies)
                    if url:
                        self.driver.get(url)
                    else:
                        self.driver.get("https://kinerja.jabarprov.go.id/kuisioner-kinerja/peer-review")
                    
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

    def extract_pegawai_from_second_page(self):
        """Extract all pegawai names from the second page (after yes/no questions)"""
        print("\n" + "="*60)
        print("=== EXTRACTING PEGAWAI NAMES (Second Page) ===")
        print("="*60)
        
        # Wait for page to load (should already be on second page after clicking Selanjutnya)
        time.sleep(3)
        
        # Use nth-child pattern to find pegawai names from second page
        print("🔍 Looking for pegawai names using nth-child pattern (second page)...")
        
        pegawai_names = []
        
        # First, wait for the form to be present
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
            )
        except TimeoutException:
            print("⚠️  Could not find form element")
            return []
        
        # Pattern explanation:
        # - form > div:nth-child(section) - sections (1, 2, 3, ...)
        # - Each section contains the same pegawai but in different positions
        # - form > div:nth-child(1) > div:nth-child(3) = first pegawai in first section
        # - form > div:nth-child(2) > div:nth-child(3) = first pegawai in second section (same name)
        # - form > div:nth-child(1) > div:nth-child(4) = second pegawai in first section
        # - form > div:nth-child(1) > div:nth-child(5) = third pegawai in first section
        # 
        # Solution: Extract from first section only, starting from div:nth-child(3) onwards
        
        # Extract pegawai names and IDs from the first section only
        # Try div indices starting from 3, 4, 5, ... until we can't find more
        pegawai_index = 3  # Start from 3 (as shown in examples)
        max_attempts = 50  # Safety limit
        attempts = 0
        
        pegawai_data = []  # Store both name and ID
        
        print("🔍 Extracting pegawai names and IDs from first section...")
        
        while attempts < max_attempts:
            name = None
            pegawai_id = None
            
            # Try to find the pegawai name in the first section at this index
            try:
                # Pattern: form > div:nth-child(1) > div:nth-child(pegawai_index) > div > div.flex.flex-col.gap-4.items-center > div > h6
                selector = f"form > div:nth-child(1) > div:nth-child({pegawai_index}) > div > div.flex.flex-col.gap-4.items-center > div > h6"
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                name = element.text.strip()
                
                if name:
                    # Try to extract pegawai ID from radio buttons in the same section
                    # Look for radio buttons with pattern: [id*="-{pegawai_id}-"]
                    # Try to find a radio button near this pegawai to extract the ID
                    try:
                        # Look for radio buttons in the same div structure
                        # Radio buttons might be: form > div:nth-child(1) > div:nth-child(pegawai_index) > ... > input[type="radio"]
                        radio_selector = f"form > div:nth-child(1) > div:nth-child({pegawai_index}) input[type='radio']"
                        radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, radio_selector)
                        
                        if radio_buttons:
                            # Get the first radio button's ID to extract pegawai_id
                            radio_id = radio_buttons[0].get_attribute("id")
                            if radio_id:
                                # Pattern: \31 435-199010262012061002-9 or 1435-199010262012061002-9
                                # Extract the middle part (pegawai_id) between dashes
                                # Remove escape sequences and split
                                clean_id = radio_id.replace("\\31 ", "").replace("\\3", "").strip()
                                parts = clean_id.split("-")
                                if len(parts) >= 2:
                                    pegawai_id = parts[1]  # Second part is the pegawai ID
                                    print(f"      Extracted ID from radio button: {pegawai_id}")
                        
                        # Alternative: try to find by looking at Question 1 radio buttons (1435)
                        if not pegawai_id:
                            # Look for radio buttons in Question 1 to extract IDs by order
                            try:
                                # Try different patterns for finding Question 1 radios
                                q1_selectors = [
                                    "input[type='radio'][id^='\\31 435-']",
                                    "input[type='radio'][id^='1435-']",
                                    "input[type='radio'][id*='1435-']",
                                ]
                                
                                all_radios = []
                                for selector in q1_selectors:
                                    try:
                                        all_radios = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        if all_radios:
                                            break
                                    except:
                                        continue
                                
                                # Get radio button at the position matching our pegawai index
                                if all_radios and len(pegawai_data) < len(all_radios):
                                    radio_id = all_radios[len(pegawai_data)].get_attribute("id")
                                    if radio_id:
                                        clean_id = radio_id.replace("\\31 ", "").replace("\\3", "").strip()
                                        parts = clean_id.split("-")
                                        if len(parts) >= 2:
                                            pegawai_id = parts[1]
                                            print(f"      Extracted ID from Q1 radio: {pegawai_id}")
                            except Exception as e:
                                pass
                    except Exception as e:
                        print(f"   ⚠️  Could not extract ID for pegawai {len(pegawai_data) + 1}: {e}")
                    
                    pegawai_data.append({"name": name, "id": pegawai_id, "index": pegawai_index})
                    print(f"   ✓ Found pegawai {len(pegawai_data)}: {name} (ID: {pegawai_id or 'not found'})")
                    pegawai_index += 1  # Move to next pegawai index
                    attempts = 0  # Reset attempts since we found one
                else:
                    # Empty name, probably no more pegawai
                    break
            except (NoSuchElementException, TimeoutException):
                # No more pegawai found, stop searching
                break
            except Exception as e:
                print(f"   ⚠️  Error extracting pegawai at div:nth-child({pegawai_index}): {e}")
                attempts += 1
                if attempts >= 3:  # If we fail 3 times in a row, probably no more pegawai
                    break
                pegawai_index += 1  # Try next index anyway
        
        # Return list of names for compatibility
        pegawai_names = [p["name"] for p in pegawai_data]
        
        # Store full data in instance variable for later use
        self.pegawai_data = pegawai_data

        if not pegawai_names:
            print("\n❌ No pegawai names found!")
            print("💡 The page structure might have changed. Please inspect the page manually.")
            return []
        
        # Filter out empty names and print results
        pegawai_names = [name for name in pegawai_names if name]
        
        print(f"\n✅ Successfully extracted {len(pegawai_names)} pegawai names:")
        for i, name in enumerate(pegawai_names, 1):
            print(f"   {i}. {name}")
        
        # Save to file
        output_file = "pegawai_names.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as file:
                for name in pegawai_names:
                    file.write(f"{name}\n")
            print(f"\n💾 Saved pegawai names to: {output_file}")
        except Exception as e:
            print(f"\n⚠️  Error saving to file: {e}")
        
        return pegawai_names
    
    def assign_scores(self, pegawai_names):
        """Assign scores to pegawai names based on user input"""
        print("\n" + "="*60)
        print("=== ASSIGNING SCORES TO PEGAWAI ===")
        print("="*60)
        
        # Display all pegawai names with numbers
        print("\n📋 Pegawai list:")
        for i, name in enumerate(pegawai_names, 1):
            print(f"   {i}. {name}")
        
        # Initialize all scores to 8 (default)
        scores = {}
        for i, name in enumerate(pegawai_names, 1):
            scores[i] = {"name": name, "score": 8}
        
        # Ask for score 9 assignments
        print("\n" + "-"*60)
        print("Score 9 assignments:")
        print("-"*60)
        try:
            score_9_input = input("Assign score 9 (enter numbers separated by comma, e.g. 1, 7, 15): ").strip()
            if score_9_input:
                score_9_numbers = [int(x.strip()) for x in score_9_input.split(",") if x.strip().isdigit()]
                for num in score_9_numbers:
                    if 1 <= num <= len(pegawai_names):
                        scores[num]["score"] = 9
                        print(f"   ✓ Assigned score 9 to: {scores[num]['name']} (#{num})")
                    else:
                        print(f"   ⚠️  Invalid number: {num} (must be between 1 and {len(pegawai_names)})")
        except ValueError:
            print("   ⚠️  Invalid input format. Skipping score 9 assignments.")
        
        # Ask for score 7 assignments
        print("\n" + "-"*60)
        print("Score 7 assignments:")
        print("-"*60)
        try:
            score_7_input = input("Assign score 7 (enter numbers separated by comma, e.g. 11): ").strip()
            if score_7_input:
                score_7_numbers = [int(x.strip()) for x in score_7_input.split(",") if x.strip().isdigit()]
                for num in score_7_numbers:
                    if 1 <= num <= len(pegawai_names):
                        scores[num]["score"] = 7
                        print(f"   ✓ Assigned score 7 to: {scores[num]['name']} (#{num})")
                    else:
                        print(f"   ⚠️  Invalid number: {num} (must be between 1 and {len(pegawai_names)})")
        except ValueError:
            print("   ⚠️  Invalid input format. Skipping score 7 assignments.")
        
        # Ask for user's own name (score 10)
        print("\n" + "-"*60)
        print("Score 10 assignment (Your own name):")
        print("-"*60)
        try:
            score_10_input = input("Enter your pegawai number for score 10 (e.g. 16): ").strip()
            if score_10_input and score_10_input.isdigit():
                num = int(score_10_input)
                if 1 <= num <= len(pegawai_names):
                    scores[num]["score"] = 10
                    print(f"   ✓ Assigned score 10 to: {scores[num]['name']} (#{num})")
                else:
                    print(f"   ⚠️  Invalid number: {num} (must be between 1 and {len(pegawai_names)})")
            else:
                print("   ⚠️  No number entered. Skipping score 10 assignment.")
        except ValueError:
            print("   ⚠️  Invalid input format. Skipping score 10 assignment.")
        
        # Display final score assignments
        print("\n📊 Final Score Assignments:")
        print("-"*60)
        for i in sorted(scores.keys()):
            print(f"   {i}. {scores[i]['name']}: {scores[i]['score']}")
        
        # Save scores to file
        output_file = "pegawai_scores.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as file:
                for i in sorted(scores.keys()):
                    file.write(f"{i}. {scores[i]['name']}: {scores[i]['score']}\n")
            print(f"\n💾 Saved score assignments to: {output_file}")
        except Exception as e:
            print(f"\n⚠️  Error saving scores to file: {e}")
        
        return scores
    
    def fill_scores(self, pegawai_scores):
        """Fill in scores by clicking radio buttons based on assigned scores"""
        print("\n" + "="*60)
        print("=== FILLING SCORES ===")
        print("="*60)
        
        # Ensure we're on the second page
        if "peer-review" not in self.driver.current_url:
            print("⚠️  Not on the correct page. Please ensure you're on the second page.")
            return False
        
        # Get pegawai data with IDs
        if not hasattr(self, 'pegawai_data') or not self.pegawai_data:
            print("⚠️  Pegawai data not available. Cannot fill scores.")
            return False
        
        # Pattern analysis:
        # Radio button ID format: \31 [question_id]-[pegawai_id]-[score]
        # Question ID starts at 1435 and increments: 1435, 1436, 1437, ...
        # We need to find how many questions there are
        
        # First, find all unique question IDs by looking at radio buttons
        try:
            all_radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][id^='\\31 ']")
            question_ids = set()
            
            for radio in all_radio_buttons:
                radio_id = radio.get_attribute("id")
                if radio_id:
                    # Extract question ID: \31 1435-... -> 1435
                    parts = radio_id.replace("\\31 ", "").split("-")
                    if len(parts) >= 1 and parts[0].isdigit():
                        question_ids.add(int(parts[0]))
            
            question_ids = sorted(list(question_ids))
            print(f"✓ Found {len(question_ids)} questions: {question_ids}")
            
            if not question_ids:
                print("⚠️  Could not find question IDs")
                return False
                
        except Exception as e:
            print(f"⚠️  Error finding questions: {e}")
            return False
        
        successful_clicks = 0
        failed_clicks = 0
        
        # Loop through each question and each pegawai
        for question_num, question_id in enumerate(question_ids, 1):
            print(f"\n📝 Processing Question {question_num} (ID: {question_id})...")
            
            for pegawai_num, pegawai_info in enumerate(self.pegawai_data, 1):
                pegawai_id = pegawai_info.get("id")
                pegawai_name = pegawai_info.get("name")
                
                if not pegawai_id:
                    print(f"   ⚠️  Pegawai {pegawai_num} ({pegawai_name}): No ID found, skipping")
                    continue
                
                # Get assigned score for this pegawai
                if pegawai_num not in pegawai_scores:
                    print(f"   ⚠️  Pegawai {pegawai_num} ({pegawai_name}): No score assigned, skipping")
                    continue
                
                assigned_score = pegawai_scores[pegawai_num]["score"]
                
                # Construct radio button ID: Pattern is [question_id]-[pegawai_id]-[score]
                # The actual ID in HTML might be: \31 [question_id]-[pegawai_id]-[score] or just [question_id]-[pegawai_id]-[score]
                # Try multiple formats
                radio_id_formats = [
                    f"{question_id}-{pegawai_id}-{assigned_score}",  # Direct format
                    f"\\31 {question_id}-{pegawai_id}-{assigned_score}",  # With escape sequence
                ]
                
                clicked = False
                
                # Try finding by ID first
                for radio_id in radio_id_formats:
                    try:
                        radio_button = WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((By.ID, radio_id))
                        )
                        radio_button.click()
                        print(f"   ✓ Q{question_num} - Pegawai {pegawai_num} ({pegawai_name[:30]}...): Score {assigned_score}")
                        time.sleep(0.2)  # Brief pause between clicks
                        successful_clicks += 1
                        clicked = True
                        break
                    except (NoSuchElementException, TimeoutException):
                        continue
                
                # If ID method didn't work, try CSS selector with pegawai_id
                if not clicked:
                    try:
                        # CSS selector: input[id*="{pegawai_id}-{score}"] for this question
                        # Match radio buttons that contain both pegawai_id and the score, and the question_id
                        alt_selector = f"input[type='radio'][id*='{question_id}-'][id*='-{pegawai_id}-'][id*='-{assigned_score}']"
                        radio_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, alt_selector))
                        )
                        radio_button.click()
                        print(f"   ✓ Q{question_num} - Pegawai {pegawai_num} ({pegawai_name[:30]}...): Score {assigned_score} (CSS selector)")
                        time.sleep(0.2)
                        successful_clicks += 1
                        clicked = True
                    except Exception as e2:
                        # Last resort: try simpler pattern matching
                        try:
                            # Just match pegawai_id and score for this question
                            simple_selector = f"input[type='radio'][id*='{pegawai_id}-{assigned_score}']"
                            # Filter to only those in this question section
                            all_matching = self.driver.find_elements(By.CSS_SELECTOR, simple_selector)
                            for rb in all_matching:
                                rb_id = rb.get_attribute("id")
                                if rb_id and f"{question_id}-" in rb_id:
                                    rb.click()
                                    print(f"   ✓ Q{question_num} - Pegawai {pegawai_num} ({pegawai_name[:30]}...): Score {assigned_score} (pattern match)")
                                    time.sleep(0.2)
                                    successful_clicks += 1
                                    clicked = True
                                    break
                        except Exception:
                            pass
                
                if not clicked:
                    print(f"   ⚠️  Q{question_num} - Pegawai {pegawai_num} ({pegawai_name[:30]}...): Could not click score {assigned_score} (ID: {pegawai_id})")
                    failed_clicks += 1
        
        print(f"\n✅ Completed filling scores:")
        print(f"   ✓ Successful: {successful_clicks}")
        if failed_clicks > 0:
            print(f"   ⚠️  Failed: {failed_clicks}")
        
        # Click "Selanjutnya" button after filling all scores
        print("\n🔘 Clicking 'Selanjutnya' button to proceed...")
        selanjutnya_clicked = self.click_selanjutnya_button()
        
        return successful_clicks > 0 and selanjutnya_clicked
    
    def click_selanjutnya_button(self):
        """Click the Selanjutnya button - reusable method"""
        try:
            # Selector: #__nuxt > div > div > div > section > section > div.mt-8.lg\:w-8\/12.pr-2.flex.justify-between > button:nth-child(2)
            # Full path selector with proper escaping
            selanjutnya_selector = "#__nuxt > div > div > div > section > section > div.mt-8.lg\\:w-8\\/12.pr-2.flex.justify-between > button:nth-child(2)"
            
            selanjutnya_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selanjutnya_selector))
            )
            selanjutnya_button.click()
            print("   ✓ Clicked 'Selanjutnya' button")
            time.sleep(2)  # Wait for page to navigate/load next step
            return True
        except (NoSuchElementException, TimeoutException) as e:
            print(f"   ⚠️  Could not find or click 'Selanjutnya' button (full path): {e}")
            # Try simpler selector pattern if full path fails
            try:
                simple_selector = "div.mt-8 > button:nth-child(2)"
                selanjutnya_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, simple_selector))
                )
                selanjutnya_button.click()
                print("   ✓ Clicked 'Selanjutnya' button (using simpler selector)")
                time.sleep(2)
                return True
            except Exception as e2:
                # Try finding by text content using XPath as last resort
                try:
                    selanjutnya_xpath = "//button[contains(text(), 'Selanjutnya')]"
                    selanjutnya_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selanjutnya_xpath))
                    )
                    selanjutnya_button.click()
                    print("   ✓ Clicked 'Selanjutnya' button (using XPath)")
                    time.sleep(2)
                    return True
                except Exception as e3:
                    print(f"   ⚠️  All methods failed: {e3}")
                    return False
    
    def add_comments_for_high_scores(self, pegawai_scores):
        """Add comments for pegawai with high scores (9 or 10)"""
        print("\n" + "="*60)
        print("=== ADDING COMMENTS FOR HIGH SCORES ===")
        print("="*60)
        
        # Wait for page to load (should be on comments page after clicking Selanjutnya)
        time.sleep(3)
        
        # Get pegawai data with IDs
        if not hasattr(self, 'pegawai_data') or not self.pegawai_data:
            print("⚠️  Pegawai data not available. Cannot add comments.")
            return False
        
        # Find pegawai with high scores (9 or 10)
        high_score_pegawai = []
        for pegawai_num, pegawai_info in enumerate(self.pegawai_data, 1):
            if pegawai_num in pegawai_scores:
                score = pegawai_scores[pegawai_num]["score"]
                if score >= 9:  # High score is 9 or 10
                    high_score_pegawai.append({
                        "num": pegawai_num,
                        "name": pegawai_info.get("name"),
                        "id": pegawai_info.get("id"),
                        "score": score
                    })
        
        if not high_score_pegawai:
            print("\n⚠️  No pegawai with high scores (9 or 10) found. Skipping comments.")
            return True
        
        print(f"\n📝 Found {len(high_score_pegawai)} pegawai with high scores:")
        for p in high_score_pegawai:
            print(f"   - {p['name']}: Score {p['score']}")
        
        successful = 0
        failed = 0
        
        # Add comments for each high-score pegawai
        for p in high_score_pegawai:
            pegawai_id = p["id"]
            pegawai_name = p["name"]
            
            if not pegawai_id:
                print(f"   ⚠️  {pegawai_name}: No ID found, skipping")
                failed += 1
                continue
            
            # Textbox ID pattern: positif-{pegawai_id}
            textbox_id = f"positif-{pegawai_id}"
            comment_text = f"{pegawai_name} sangat baik"
            
            try:
                # Find textbox by ID
                textbox = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, textbox_id))
                )
                
                # Clear and fill textbox
                textbox.clear()
                textbox.send_keys(comment_text)
                print(f"   ✓ Added comment for {pegawai_name[:30]}...: '{comment_text}'")
                time.sleep(0.3)  # Brief pause between fills
                successful += 1
                
            except (NoSuchElementException, TimeoutException) as e:
                print(f"   ⚠️  {pegawai_name[:30]}...: Could not find textbox (ID: {textbox_id})")
                failed += 1
            except Exception as e:
                print(f"   ⚠️  {pegawai_name[:30]}...: Error - {e}")
                failed += 1
        
        print(f"\n✅ Completed adding comments:")
        print(f"   ✓ Successful: {successful}")
        if failed > 0:
            print(f"   ⚠️  Failed: {failed}")
        
        # Click "Selesai dan Kirim" button
        print("\n🔘 Clicking 'Selesai dan Kirim' button...")
        time.sleep(2)
        
        # Try multiple selectors in order
        selectors = [
            (By.CSS_SELECTOR, "#__nuxt > div > div > div > section > section > div.mt-8.lg\\:w-8\\/12.pr-2.flex.justify-between > button:nth-child(2)"),
            (By.XPATH, "//*[@id=\"__nuxt\"]/div/div/div/section/section/div[2]/button[2]"),
            (By.XPATH, "//button[contains(@class, 'bg-green-700') and contains(text(), 'Selesai')]"),
            (By.XPATH, "//button[contains(text(), 'Selesai') or contains(text(), 'Kirim')]"),
        ]
        
        for by, selector in selectors:
            try:
                # Wait for button to be present and enabled
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Check if button is disabled
                is_disabled = submit_button.get_attribute("disabled") is not None
                if is_disabled:
                    print(f"   ⚠️  Button found but is disabled, waiting...")
                    # Wait for button to become enabled
                    WebDriverWait(self.driver, 10).until(
                        lambda d: submit_button.get_attribute("disabled") is None
                    )
                
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                time.sleep(0.5)
                
                # Try regular click first
                try:
                    submit_button.click()
                    print(f"   ✓ Clicked 'Selesai dan Kirim' button (using {by})")
                    time.sleep(2)
                    return True
                except Exception:
                    # Fallback to JavaScript click
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    print(f"   ✓ Clicked 'Selesai dan Kirim' button using JavaScript (using {by})")
                    time.sleep(2)
                    return True
                    
            except (NoSuchElementException, TimeoutException):
                continue
        
        # If all selectors failed
        print(f"   ⚠️  Could not find or click 'Selesai dan Kirim' button with any selector")
        return successful > 0  # Return True if comments were added even if button click failed
    
    def click_random_buttons_until_done(self):
        """Randomly click between left and right buttons until no buttons are found"""
        print("\n" + "="*60)
        print("=== CLICKING RANDOM BUTTONS ===")
        print("="*60)
        print("\n📋 Will randomly click between left and right buttons")
        print("   until no buttons are available...")
        
        import random
        max_attempts = 600  # Safety limit to prevent infinite loops
        click_count = 0
        consecutive_not_found = 0
        max_not_found = 3  # If buttons not found this many times in a row, assume done
        
        button_container_selector = "div.grid.grid-cols-2.gap-6"
        left_button_selector = f"{button_container_selector} > div:nth-child(1)"
        right_button_selector = f"{button_container_selector} > div:nth-child(2)"
        
        while click_count < max_attempts:
            try:
                # Wait a moment for page to load (especially after previous click)
                # time.sleep(0.5)
                
                # Check if buttons exist
                try:
                    button_container = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, button_container_selector))
                    )
                    
                    # Check if both buttons exist
                    left_button = None
                    right_button = None
                    
                    try:
                        left_button = self.driver.find_element(By.CSS_SELECTOR, left_button_selector)
                    except NoSuchElementException:
                        pass
                    
                    try:
                        right_button = self.driver.find_element(By.CSS_SELECTOR, right_button_selector)
                    except NoSuchElementException:
                        pass
                    
                    # If no buttons found, increment counter and check again
                    if not left_button and not right_button:
                        consecutive_not_found += 1
                        if consecutive_not_found >= max_not_found:
                            print(f"\n✅ No buttons found after {consecutive_not_found} checks. Assuming done!")
                            break
                        print(f"   ⏳ Buttons not found, waiting... (attempt {consecutive_not_found}/{max_not_found})")
                        time.sleep(3)  # Wait longer before retrying
                        continue
                    
                    # Reset counter since we found buttons
                    consecutive_not_found = 0
                    
                    # Randomly choose which button to click (if both exist)
                    if left_button and right_button:
                        button_to_click = random.choice([left_button, right_button])
                        button_name = "left" if button_to_click == left_button else "right"
                    elif left_button:
                        button_to_click = left_button
                        button_name = "left"
                    elif right_button:
                        button_to_click = right_button
                        button_name = "right"
                    else:
                        continue
                    
                    # Click the selected button
                    button_to_click.click()
                    click_count += 1
                    print(f"   ✓ Click {click_count}: Clicked {button_name} button")
                    # time.sleep(1)  # Wait for page to load/transition
                    
                except TimeoutException:
                    # Container not found, check if we're done
                    consecutive_not_found += 1
                    if consecutive_not_found >= max_not_found:
                        print(f"\n✅ No button container found after {consecutive_not_found} checks. Assuming done!")
                        break
                    print(f"   ⏳ Button container not found, waiting... (attempt {consecutive_not_found}/{max_not_found})")
                    time.sleep(3)
                    continue
                    
            except Exception as e:
                print(f"   ⚠️  Error during button clicking: {e}")
                consecutive_not_found += 1
                if consecutive_not_found >= max_not_found:
                    print(f"\n⚠️  Too many errors. Stopping.")
                    break
                time.sleep(3)
                continue
        
        if click_count >= max_attempts:
            print(f"\n⚠️  Reached maximum attempts ({max_attempts}). Stopping.")
        
        print(f"\n✅ Completed random button clicking:")
        print(f"   ✓ Total clicks: {click_count}")
        
        return click_count > 0
    
    def answer_yes_no_questions(self, num_pegawai):
        """Answer yes/no questions for each pegawai: Kenal (first) and Tidak (second)"""
        print("\n" + "="*60)
        print("=== ANSWERING YES/NO QUESTIONS ===")
        print("="*60)
        print(f"\n📋 Processing {num_pegawai} pegawai(s)...")
        print("   Question 1: Always click 'Kenal'")
        print("   Question 2: Always click 'Tidak'")
        
        # Wait for form to be ready
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
            )
        except TimeoutException:
            print("⚠️  Form not found")
            return False
        
        # Find all form > div children (same pattern as extracting names)
        try:
            form_divs = self.driver.find_elements(By.CSS_SELECTOR, "form > div")
            print(f"✓ Found {len(form_divs)} form div children")
        except Exception as e:
            print(f"⚠️  Error finding form divs: {e}")
            return False
        
        successful = 0
        failed = 0
        
        # Loop through each nth-child to answer questions
        for i in range(1, len(form_divs) + 1):
            try:
                # Click "Kenal" button (first question)
                # Selector: form > div:nth-child(n) > div > div:nth-child(3) > div > button:nth-child(1)
                kenal_selector = f"form > div:nth-child({i}) > div > div:nth-child(3) > div > button:nth-child(1)"
                
                kenal_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, kenal_selector))
                    # EC.presence_of_element_located((By.LINK_TEXT, "Kenal"))
                )
                kenal_button.click()
                print(f"   ✓ Pegawai {i}: Clicked 'Kenal'")
                time.sleep(0.5)  # Brief pause between clicks
                
                # Click "Tidak" button (second question)
                # Selector: form > div:nth-child(n) > div > div:nth-child(5) > div > button:nth-child(2)
                tidak_selector = f"form > div:nth-child({i}) > div > div:nth-child(5) > div > button:nth-child(2)"
                
                tidak_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, tidak_selector))
                    # EC.presence_of_element_located((By.LINK_TEXT, "Tidak"))
                )
                tidak_button.click()
                print(f"   ✓ Pegawai {i}: Clicked 'Tidak'")
                time.sleep(0.5)  # Brief pause before next pegawai
                
                successful += 1
                
            except (NoSuchElementException, TimeoutException) as e:
                print(f"   ⚠️  Pegawai {i}: Could not find buttons - {e}")
                failed += 1
                continue
            except Exception as e:
                print(f"   ⚠️  Pegawai {i}: Error - {e}")
                failed += 1
                continue
        
        print(f"\n✅ Completed answering questions:")
        print(f"   ✓ Successful: {successful}")
        if failed > 0:
            print(f"   ⚠️  Failed: {failed}")
        
        # Click "Selanjutnya" button after answering all questions
        print("\n🔘 Clicking 'Selanjutnya' button...")
        selanjutnya_clicked = self.click_selanjutnya_button()
        
        return successful > 0 and selanjutnya_clicked
    
    def test_20251103Kuesioner(self):
      
      # Try to load saved cookies first
      cookies_loaded = self.load_cookies()
      
      if not cookies_loaded:
          print("❌ No peer-review cookies found!")
          print("💡 Please extract peer-review cookies first using:")
          print("   python3 extract_peer_review_cookies.py")
          raise Exception("No peer-review cookies found. Please extract cookies using 'python3 extract_peer_review_cookies.py'")
      else:
          print("✓ Loaded saved cookies - skipping manual login")
          time.sleep(2)  # Brief pause to ensure page is loaded
      
      # Navigate to kuesioner page (first page with yes/no questions)
      print("\n🌐 Navigating to kuesioner page...")
      kuesioner_url = "https://kinerja.jabarprov.go.id/kuisioner-kinerja/peer-review"
      self.driver.get(kuesioner_url)
      time.sleep(3)
      
      # First: Answer yes/no questions (indiscriminate, doesn't need names)
      # Find number of pegawai by counting form divs
      try:
          WebDriverWait(self.driver, 10).until(
              EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
          )
          form_divs = self.driver.find_elements(By.CSS_SELECTOR, "form > div")
          num_pegawai = len(form_divs)
          print(f"✓ Found {num_pegawai} pegawai entries on first page")
      except Exception as e:
          print(f"⚠️  Error finding form divs: {e}")
          num_pegawai = 0
      
      if num_pegawai == 0:
          print("\n⚠️  Could not determine number of pegawai. Trying click random buttons ")
          buttons_clicked = self.click_random_buttons_until_done()
          if not buttons_clicked:
              print("\n⚠️  Failed to click random buttons. Please check manually.")
              return
          else:
              print("\n✅ Random buttons clicked successfully.")
              return
      
      # Answer yes/no questions for all pegawai
      questions_answered = self.answer_yes_no_questions(num_pegawai)
      
      if not questions_answered:
          print("\n⚠️  Failed to answer yes/no questions. Please check manually.")
          return
      
      # After clicking Selanjutnya, we should be on the second page
      # Extract pegawai names from second page
      pegawai_names = self.extract_pegawai_from_second_page()
      
      if not pegawai_names:
          print("\n⚠️  No pegawai names collected from second page. Cannot proceed with automation.")
          return
      
      # Assign scores to pegawai names (from second page)
      # If pegawai_scores.txt exists, load from file, otherwise assign interactively
      if os.path.exists("pegawai_scores.txt"):
          print("\n✅ Pegawai scores already assigned. Loading from file...")
          # Load scores from file
          pegawai_scores = {}
          try:
              with open("pegawai_scores.txt", "r", encoding="utf-8") as file:
                  for line in file:
                      # Format: "1. Name: 8"
                      parts = line.strip().split(": ")
                      if len(parts) == 2:
                          num_part = parts[0].split(". ")[0]
                          if num_part.isdigit():
                              num = int(num_part)
                              name = parts[0].split(". ", 1)[1] if ". " in parts[0] else ""
                              score = int(parts[1]) if parts[1].isdigit() else 8
                              pegawai_scores[num] = {"name": name, "score": score}
              print(f"📋 Loaded scores for {len(pegawai_scores)} pegawai(s)")
          except Exception as e:
              print(f"⚠️  Error loading scores from file: {e}")
              print("📋 Assigning scores interactively instead...")
              pegawai_scores = self.assign_scores(pegawai_names)
      else:
          print("\n📋 Assigning scores to pegawai names...")
          pegawai_scores = self.assign_scores(pegawai_names)
          print("\n✅ Scores assigned to pegawai names!")
      
      # Fill scores by clicking radio buttons
      scores_filled = self.fill_scores(pegawai_scores)
      
      if not scores_filled:
          print("\n⚠️  Failed to fill scores. Please check manually.")
          return
      
      print("\n✅ Score filling complete!")
      
      # After clicking Selanjutnya, we should be on the comments page
      # Add comments for high-score pegawai
      comments_added = self.add_comments_for_high_scores(pegawai_scores)
      
      if not comments_added:
          print("\n⚠️  Failed to add comments. Please check manually.")
          return
      
      print("\n✅ Comments added and form submitted!")
      
      # After clicking "Selesai dan Kirim", there may be random buttons to click
      # Click randomly between left and right buttons until done
      buttons_clicked = self.click_random_buttons_until_done()
      
      print(f"\n🎉 Automation complete for {len(pegawai_names)} pegawai(s)!")