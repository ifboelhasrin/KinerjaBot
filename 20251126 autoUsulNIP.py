import csv
import pytest
import time
from datetime import datetime
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class TestUsulNIP:
    LOGIN_URL = "https://sso-siasn.bkn.go.id/auth/realms/public-siasn/protocol/openid-connect/auth?client_id=bkn-portal&redirect_uri=https%3A%2F%2Fasndigital.bkn.go.id%2F&state=340c403d-b082-466a-85fb-e5b511e15178&response_mode=fragment&response_type=code&scope=openid&nonce=a8f8d870-8397-4355-b0e4-9b5994a25e6e&code_challenge=e2uUvrV_MrgGMPdyEXRkQ3MjxeLRro2-bClPQD152V8&code_challenge_method=S256"
    TARGET_URL = "https://siasn-instansi.bkn.go.id/tampilanData"
    COOKIE_FILE = "siasn_cookies.pkl"

    @pytest.fixture(autouse=True)
    # SAFARI BROWSER
    def setup(self):
        self.driver = webdriver.Safari()
        self.driver.maximize_window()
        yield
        self.driver.quit()

    def save_cookies(self):
        """Save current browser cookies to disk for later reuse."""
        import pickle
        try:
            cookies = self.driver.get_cookies()
            with open(self.COOKIE_FILE, "wb") as fh:
                pickle.dump(cookies, fh)
            print(f"💾 Saved {len(cookies)} cookies to {self.COOKIE_FILE}")
        except Exception as exc:
            print(f"⚠️  Failed to save cookies: {exc}")

    def load_cookies(self, url=None) -> bool:
        """Load cookies from disk and apply them to the given URL (or TARGET_URL)."""
        import os
        import pickle

        cookie_path = self.COOKIE_FILE
        if not os.path.exists(cookie_path):
            print(f"ℹ️ Cookie file not found: {cookie_path}")
            return False

        target = url or self.TARGET_URL
        print(f"🌐 Opening {target} before loading cookies...")
        self.driver.get(target)

        try:
            with open(cookie_path, "rb") as fh:
                cookies = pickle.load(fh)
        except Exception as exc:
            print(f"⚠️  Could not read cookie file: {exc}")
            return False

        applied = 0
        for cookie in cookies:
            try:
                cookie = {k: v for k, v in cookie.items() if v is not None}
                self.driver.add_cookie(cookie)
                applied += 1
            except Exception as exc:
                print(f"   ⚠️  Could not add cookie {cookie.get('name')}: {exc}")

        self.driver.refresh()
        print(f"✓ Applied {applied} cookies from {cookie_path}")
        return applied > 0

    def wait_for_login_form(self, timeout: int = 5):
        """Wait until the SIASN login form is visible."""
        login_selectors = [
            (By.NAME, "username"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//button[contains(., 'Masuk') or contains(., 'Login')]"),
        ]

        for selector in login_selectors:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(selector)
                )
                print("✓ Login form detected. Please complete authentication manually.")
                return
            except TimeoutException:
                continue

        raise TimeoutException("Login form did not appear in time.")

    def wait_for_monitoring_dashboard(self, timeout: int = 5):
        """Wait until the Monitoring Usulan dashboard is visible."""
        dashboard_selectors = [
            (By.XPATH, "//h1[contains(., 'Monitoring Usulan')]"),
            (By.CSS_SELECTOR, "[data-testid='table-monitoring-usulan']"),
            (By.CSS_SELECTOR, "table"),
        ]

        for selector in dashboard_selectors:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(selector)
                )
                print("✓ Monitoring dashboard detected.")
                return
            except TimeoutException:
                continue

        raise TimeoutException("Monitoring dashboard did not load in time.")

    def prompt_credentials(self):
        """Prompt user for login credentials via console."""
        print("\n🔐 Please enter your SIASN login credentials.")
        username = input("Username (email/NIP): ").strip()
        password = getpass("Password: ")
        if not username or not password:
            raise AssertionError("Username and password are required.")
        return username, password

    def fill_login_form(self, username: str, password: str):
        """Fill the login form inputs and submit."""
        username_selectors = [
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Sign In')]"),
            (By.ID, "kc-login"),
        ]

        def fill_field(selectors, value, label):
            last_error = None
            for by, locator in selectors:
                try:
                    field = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((by, locator))
                    )
                    field.clear()
                    field.send_keys(value)
                    print(f"   ✓ Filled {label}")
                    return
                except Exception as err:
                    last_error = err
            raise TimeoutException(f"Could not locate {label}: {last_error}")

        fill_field(username_selectors, username, "username")
        fill_field(password_selectors, password, "password")

        last_error = None
        for by, locator in submit_selectors:
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, locator))
                )
                button.click()
                print("   ✓ Clicked login button")
                return
            except Exception as err:
                last_error = err
        raise TimeoutException(f"Could not click login button: {last_error}")

    def prompt_otp_code(self):
        """Prompt user for the OTP code delivered to their device."""
        print("\n🔑 OTP verification required.")
        otp_code = input("Enter OTP code: ").strip()
        if not otp_code:
            raise AssertionError("OTP code cannot be empty.")
        return otp_code

    def fill_otp_form(self, otp_code: str):
        """Fill the OTP input and submit the form."""
        otp_selectors = [
            (By.NAME, "otp"),
            (By.ID, "otp"),
            (By.CSS_SELECTOR, "input[name='otp']"),
            (By.CSS_SELECTOR, "input[type='number']"),
        ]
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.ID, "kc-login"),
            (By.XPATH, "//button[contains(., 'Sign In')]"),
        ]

        last_error = None
        otp_field = None
        for by, locator in otp_selectors:
            try:
                otp_field = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, locator))
                )
                break
            except Exception as err:
                last_error = err
        if not otp_field:
            raise TimeoutException(f"Could not locate OTP field: {last_error}")

        otp_field.clear()
        otp_field.send_keys(otp_code)
        print("   ✓ Filled OTP field")

        last_error = None
        for by, locator in submit_selectors:
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, locator))
                )
                button.click()
                print("   ✓ Submitted OTP")
                return
            except Exception as err:
                last_error = err
        raise TimeoutException(f"Could not submit OTP: {last_error}")

    def handle_otp_if_present(self):
        """Detect OTP challenge, prompt user, and submit the code if required."""
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='otp'], #otp"))
            )
        except TimeoutException:
            print("   ℹ️ No OTP challenge detected.")
            return False

        otp_code = self.prompt_otp_code()
        self.fill_otp_form(otp_code)
        return True

    def wait_for_post_login_redirect(self, timeout: int = 5):
        """Wait until the login redirect completes (away from SSO host), if it happens."""

        def redirected(driver):
            current = driver.current_url.lower()
            return "sso-siasn" not in current and "keycloak" not in current

        try:
            WebDriverWait(self.driver, timeout).until(redirected)
            print("   ✓ Login redirect completed.")
        except TimeoutException:
            print("   ℹ️ Login redirect not detected within timeout, continuing anyway.")

    def open_monitoring_page(self):
        """Drive the login flow, then hover 'start' and click 'Layanan Instansi'."""
        print(f"🌐 Opening SIASN login URL...")
        self.driver.get(self.LOGIN_URL)
        time.sleep(2)

        try:
            self.wait_for_login_form(timeout=2)
            username, password = self.prompt_credentials()
            self.fill_login_form(username, password)
            self.handle_otp_if_present()
            self.wait_for_post_login_redirect()
        except TimeoutException:
            print("ℹ️ Login form not detected; assuming an existing session.")

        # At this point we assume the user is authenticated in the current domain.
        # Optionally persist cookies for future re-use.
        self.save_cookies()

        # Wait for the SIASN landing page to stabilise
        print("⏳ Waiting for SIASN landing page after login...")
        time.sleep(5)

        # Hover on //*[@id="start"]
        start_xpath = '//*[@id="start"]'
        try:
            start_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, start_xpath))
            )
            ActionChains(self.driver).move_to_element(start_elem).perform()
            print("   ✓ Hovered on 'start' element.")
        except TimeoutException as exc:
            raise TimeoutException(f"Could not find 'start' element at {start_xpath}: {exc}")

        # Press //*[@id="btn-layanan-instansi"]
        layanan_xpath = '//*[@id="btn-layanan-instansi"]'
        try:
            # Ensure the button is visible
            layanan_btn = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, layanan_xpath))
            )
            # Scroll into view to avoid overlays / off-screen issues
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", layanan_btn
            )
            time.sleep(0.5)
            # Wait until it's clickable again
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, layanan_xpath))
            )
            # Use ActionChains click to reduce interception issues
            ActionChains(self.driver).move_to_element(layanan_btn).click().perform()
            print("   ✓ Clicked 'Layanan Instansi' button.")
        except TimeoutException as exc:
            raise TimeoutException(
                f"Could not find or click 'Layanan Instansi' button at {layanan_xpath}: {exc}"
            )

        # Wait for animation / submenu to appear, then click second menu item
        print("⏳ Waiting for Layanan Instansi menu animation...")
        time.sleep(2)

        submenu_xpath = '//*[@id="menu-instansi"]/li[2]/a'
        try:
            submenu_elem = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, submenu_xpath))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", submenu_elem
            )
            time.sleep(0.5)
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, submenu_xpath))
            )
            ActionChains(self.driver).move_to_element(submenu_elem).click().perform()
            print("   ✓ Clicked second item in 'menu-instansi'.")
        except TimeoutException as exc:
            raise TimeoutException(
                f"Could not find or click menu item at {submenu_xpath}: {exc}"
            )

        # After submenu opens, click card on intro section
        card_xpath = '//*[@id="intro"]/div/div/div/div/div[3]/div[1]/div[5]'
        try:
            print("⏳ Waiting for intro card to appear...")
            card_elem = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, card_xpath))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", card_elem
            )
            time.sleep(0.5)
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, card_xpath))
            )
            ActionChains(self.driver).move_to_element(card_elem).click().perform()
            print("   ✓ Clicked intro card in third row.")
        except TimeoutException as exc:
            raise TimeoutException(
                f"Could not find or click intro card at {card_xpath}: {exc}"
            )

        print("⏳ Waiting for list page to load before clicking filter...")
        time.sleep(3)

        # Click the filter button on the tampilanData page
        filter_xpath = '//*[@id="__next"]/div/div[4]/div[3]/div/div'
        try:
            filter_btn = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, filter_xpath))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", filter_btn
            )
            time.sleep(0.5)
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, filter_xpath))
            )
            ActionChains(self.driver).move_to_element(filter_btn).click().perform()
            print("   ✓ Clicked filter button on tampilanData page.")
        except TimeoutException as exc:
            raise TimeoutException(
                f"Could not find or click filter button at {filter_xpath}: {exc}"
            )

        print("✅ Login + Layanan Instansi + submenu + card + filter click done. Ready for the hard part...")
        time.sleep(3)

    def process_usul_records_from_csv(self, csv_path: str = "testUsul.csv"):
        """Loop over testUsul.csv and process each usul record via the filter form."""
        print(f"📄 Loading usul records from {csv_path}...")
        try:
            with open(csv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh, delimiter=";")
                rows = [row for row in reader if row.get("no_urut") and row.get("no_peserta")]
        except Exception as exc:
            raise AssertionError(f"Could not read {csv_path}: {exc}")

        print(f"✓ Found {len(rows)} usul record(s) to process.")

        log_path = "testUsul_log.csv"
        # Write log header if file is empty or does not exist
        try:
            import os

            need_header = not os.path.exists(log_path) or os.path.getsize(log_path) == 0
            with open(log_path, mode="a", newline="", encoding="utf-8") as log_fh:
                writer = csv.writer(log_fh)
                if need_header:
                    writer.writerow(
                        ["timestamp", "no_urut", "no_peserta", "status", "details"]
                    )
        except Exception as exc:
            print(f"⚠️ Could not prepare log file {log_path}: {exc}")

        def log_result(no_urut_val: str, no_peserta_val: str, status: str, details: str):
            """Append one line to the usul log CSV."""
            try:
                with open(log_path, mode="a", newline="", encoding="utf-8") as log_fh:
                    writer = csv.writer(log_fh)
                    writer.writerow(
                        [
                            datetime.now().isoformat(timespec="seconds"),
                            no_urut_val,
                            no_peserta_val,
                            status,
                            details,
                        ]
                    )
            except Exception as exc:
                print(f"⚠️ Could not write to log file {log_path}: {exc}")

        for idx, row in enumerate(rows, start=1):
            no_urut = row["no_urut"].strip()
            no_peserta = row["no_peserta"].strip()
            print(f"\n===== Processing record {idx}: no_urut={no_urut}, no_peserta={no_peserta} =====")

            # 1. Input nomor peserta in //*[@id="noPeserta"]
            peserta_xpath = '//*[@id="noPeserta"]'
            try:
                peserta_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, peserta_xpath))
                )
                peserta_input.clear()
                peserta_input.send_keys(no_peserta)
                print("   ✓ Filled nomor peserta.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not find nomor peserta field: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 1: noPeserta field not found: {exc}")
                continue

            # 2. Press the cari button
            cari_xpath = '//*[@id="__next"]/div/div[4]/div[3]/div/div/div[2]/div/div[3]/button[1]'
            try:
                cari_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, cari_xpath))
                )
                cari_btn.click()
                print("   ✓ Clicked Cari button.")
                time.sleep(2)
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click Cari button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 2: Cari button not clickable: {exc}")
                continue

            # 3. Validate the result row matches no_peserta, then click checkbox
            # First, check that the third column (td:nth-child(3)) contains the expected no_peserta
            cell_selector = (
                "#__next > div > div.container > div:nth-child(4) "
                "> div.ant-table-wrapper > div > div > div > div > div "
                "> table > tbody > tr > td:nth-child(3)"
            )
            checkbox_selector = (
                "#__next > div > div.container > div:nth-child(4) "
                "> div.ant-table-wrapper > div > div > div > div > div "
                "> table > tbody > tr > td.ant-table-cell.ant-table-selection-column > label"
            )
            try:
                # Scroll down a bit to make sure the table area is visible
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(0.3)

                # Validate the third column content matches no_peserta
                cell_elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, cell_selector))
                )
                cell_text = cell_elem.text.strip()
                if cell_text != no_peserta:
                    print(f"   ⚠️ Mismatch: table shows '{cell_text}' but expected '{no_peserta}'")
                    log_result(
                        no_urut,
                        no_peserta,
                        "ERROR",
                        f"Step 3: no_peserta mismatch - table shows '{cell_text}' but expected '{no_peserta}'",
                    )
                    continue
                print(f"   ✓ Verified table row matches no_peserta: {no_peserta}")

                # Now click the checkbox
                checkbox = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, checkbox_selector))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", checkbox
                )
                time.sleep(0.3)
                checkbox.click()
                print("   ✓ Selected result checkbox.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not find table cell or checkbox: {exc}")
                log_result(
                    no_urut,
                    no_peserta,
                    "ERROR",
                    f"Step 3: table cell or checkbox not found: {exc}",
                )
                continue

            # 4. Press the button to proceed
            proceed_xpath = '//*[@id="__next"]/div/div[4]/div[5]/div/button'
            try:
                proceed_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, proceed_xpath))
                )
                proceed_btn.click()
                print("   ✓ Clicked proceed button.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click proceed button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 4: proceed button not clickable: {exc}")
                continue

            # 5. Change the tab
            tab_xpath = '//*[@id="__next"]/div/div[4]/nav/a[2]'
            try:
                tab_elem = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, tab_xpath))
                )
                tab_elem.click()
                print("   ✓ Switched to second tab.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not switch to second tab: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 5: could not change tab: {exc}")
                continue

            # 6. Put no_urut in the form
            time.sleep(0.5)
            no_urut_xpath = '//*[@id="__next"]/div/div[4]/div[4]/div[2]/div/div/div/div[1]/form/div/div[1]/div/input'
            try:
                no_urut_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, no_urut_xpath))
                )
                no_urut_input.clear()
                no_urut_input.send_keys(no_urut)
                print("   ✓ Filled no_urut.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not fill no_urut: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 6: no_urut input not available: {exc}")
                continue

            # 7. Put date 17/11/2025 in the HTML5 date input (type="date" expects YYYY-MM-DD)
            # Underneath the Safari UI, this is just a single <input type="date" ...>.
            time.sleep(0.5)
            date_input_xpath = '//*[@id="__next"]/div/div[4]/div[4]/div[2]/div/div/div/div[1]/form/div/div[3]/div/input'
            try:
                date_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, date_input_xpath))
                )
                # Use the native "value" property setter so any JS framework sees the change
                target_value = "2025-11-17"
                self.driver.execute_script(
                    """
                    const el = arguments[0];
                    const value = arguments[1];
                    const proto = Object.getPrototypeOf(el);
                    const desc = Object.getOwnPropertyDescriptor(proto, 'value');
                    desc.set.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    """,
                    date_input,
                    target_value,
                )
                current_val = date_input.get_attribute("value")
                print(f"   ✓ Date input value now: {current_val!r}")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not find date input: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 7: date input not available: {exc}")
                continue
            except Exception as exc:
                print(f"   ⚠️ Could not set date input value: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 7: error setting date value: {exc}")
                continue

            # 8. Choose option[5] from dropdown
            time.sleep(0.5)
            select_xpath = '//*[@id="__next"]/div/div[4]/div[4]/div[2]/div/div/div/div[1]/form/div/div[4]/div/select'
            option_xpath = '//*[@id="__next"]/div/div[4]/div[4]/div[2]/div/div/div/div[1]/form/div/div[4]/div/select/option[5]'
            try:
                select_elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, select_xpath))
                )
                # Try using Select first
                try:
                    select_obj = Select(select_elem)
                    select_obj.select_by_index(4)  # option[5] is index 4 (0-based)
                    print("   ✓ Selected option[5] in dropdown using Select.")
                except Exception:
                    # Fallback: click the option element directly
                    option_elem = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    option_elem.click()
                    print("   ✓ Selected option[5] in dropdown by clicking option directly.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not find dropdown or option: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 8: dropdown/option not found: {exc}")
                continue
            except Exception as exc:
                print(f"   ⚠️ Could not select dropdown option: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 8: could not select dropdown option: {exc}")
                continue

            # 9. Press the submit button
            submit_xpath = '//*[@id="__next"]/div/div[4]/div[4]/div[2]/div/div/div/div[1]/form/button'
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, submit_xpath))
                )
                submit_btn.click()
                print("   ✓ Submitted usul form.")
                time.sleep(2)
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click submit button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 9: submit button not clickable: {exc}")
                continue

            # 10. After 2 seconds, handle three confirmation popups
            time.sleep(2)

            # First button: //*[@id="__next"]/div/div[4]/div[5]/div/button[3]
            confirm1_xpath = '//*[@id="__next"]/div/div[4]/div[5]/div/button[3]'
            try:
                confirm1_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, confirm1_xpath))
                )
                confirm1_btn.click()
                print("   ✓ Clicked first confirmation button.")
                
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click first confirmation button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 10.1: first confirmation button: {exc}")
                continue

            # Second popup: /html/body/div[3]/div/div/div[3]/button[2]
            confirm2_xpath = "/html/body/div[3]/div/div/div[3]/button[2]"
            try:
                confirm2_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, confirm2_xpath))
                )
                confirm2_btn.click()
                print("   ✓ Clicked second confirmation button.")
                time.sleep(1)
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click second confirmation button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 10.2: second confirmation button: {exc}")
                continue

            # Third popup: /html/body/div[3]/div/div[3]/button[1]
            confirm3_xpath = "/html/body/div[3]/div/div[3]/button[1]"
            try:
                confirm3_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, confirm3_xpath))
                )
                confirm3_btn.click()
                print("   ✓ Clicked third confirmation button.")
                time.sleep(1)
            except TimeoutException as exc:
                print(f"   ⚠️ Could not click third confirmation button: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 10.3: third confirmation button: {exc}")
                continue

            # Re-open the filter for the next record
            filter_xpath = '//*[@id="__next"]/div/div[4]/div[3]/div/div'
            try:
                filter_btn = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, filter_xpath))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", filter_btn
                )
                time.sleep(0.5)
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, filter_xpath))
                )
                ActionChains(self.driver).move_to_element(filter_btn).click().perform()
                print("   ✓ Re-opened filter dialog for next record.")
            except TimeoutException as exc:
                print(f"   ⚠️ Could not re-open filter dialog: {exc}")
                log_result(no_urut, no_peserta, "ERROR", f"Step 10.4: could not re-open filter: {exc}")
                continue

            # If we reached here, all steps for this record succeeded
            log_result(no_urut, no_peserta, "SUCCESS", "All steps completed successfully.")

        print("\n✅ Finished processing all usul records from CSV. Waiting for integrity check...")
        time.sleep(5)

    def test_20251126UsulNIP(self):
        """End-to-end usul automation: login, navigate, and process CSV-driven records."""
        print("🚀 Starting SIASN login + Layanan Instansi + usul processing flow...")
        try:
            self.open_monitoring_page()
        except TimeoutException as exc:
            raise AssertionError(f"Monitoring page could not be opened: {exc}")

        # After navigation is complete and filter dialog is open, process CSV records
        self.process_usul_records_from_csv("testUsul.csv")