from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime, timedelta
import time
import random
import config


def _pause(min_s=0.8, max_s=2.2):
    time.sleep(random.uniform(min_s, max_s))


def _human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.06, 0.2))


def _move_and_click(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).pause(random.uniform(0.3, 0.8)).click().perform()


def _wait_for_cloudflare(driver, timeout=35):
    """Poll until Cloudflare challenge clears or timeout."""
    print("Cloudflare detected — waiting for it to clear...")
    start = time.time()
    while time.time() - start < timeout:
        title = driver.title.lower()
        if "just a moment" in title or "verifying" in title or "checking" in title:
            time.sleep(2)
        else:
            print("Cloudflare cleared.")
            return True
    print("Cloudflare did not clear in time.")
    return False


def _parse_posted_time(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p %d-%b-%y")
    except Exception:
        return None


def _search_query(driver, wait, query, seen, cutoff):
    try:
        driver.get("https://www.nvoids.com/index.jsp")
    except TimeoutException:
        # Page load timed out — check if Cloudflare is holding it
        pass

    # Detect and wait out Cloudflare
    title = driver.title.lower()
    if "just a moment" in title or "verifying" in title or "checking" in title:
        if not _wait_for_cloudflare(driver):
            return []

    _pause(2, 4)

    driver.execute_script("""
        var frames = document.querySelectorAll("iframe");
        frames.forEach(f => { try { f.remove(); } catch(e) {} });
    """)

    driver.execute_script(f"window.scrollBy(0, {random.randint(80, 200)});")
    _pause(0.5, 1.2)
    driver.execute_script("window.scrollTo(0, 0);")
    _pause(0.4, 0.9)

    try:
        search_box = wait.until(EC.element_to_be_clickable((By.ID, "search_id")))
    except TimeoutException:
        print(f"Search box not found for '{query}' — page may still be blocked.")
        return []

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_box)
    _pause(0.5, 1.0)

    _move_and_click(driver, search_box)
    _pause(0.3, 0.7)
    search_box.clear()
    _pause(0.2, 0.5)

    _human_type(search_box, query)
    print(f"Typed query: {query}")
    _pause(0.8, 1.8)

    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
    _pause(0.4, 0.9)

    _move_and_click(driver, submit_btn)
    print("Clicked Submit")
    _pause(3.5, 6.0)

    driver.execute_script(f"window.scrollBy(0, {random.randint(150, 350)});")
    _pause(0.5, 1.2)

    rows = driver.find_elements(By.XPATH, "//tr[.//a[contains(@href, 'job_details.jsp')]]")
    jobs = []
    skipped_old = 0

    for row in rows:
        try:
            a = row.find_element(By.XPATH, ".//a[contains(@href, 'job_details.jsp')]")
            title = a.text.strip()
            href = a.get_attribute("href")

            if not title or not href or href in seen:
                continue

            cells = row.find_elements(By.TAG_NAME, "td")
            posted_at = None
            if cells:
                time_text = cells[-1].text.strip()
                posted_at = _parse_posted_time(time_text)

            if posted_at and posted_at < cutoff:
                skipped_old += 1
                continue

            seen.add(href)
            jobs.append({"title": title, "link": href, "posted_at": posted_at})

        except Exception as e:
            print(f"Error processing job row: {e}")

    if skipped_old:
        print(f"Filtered out {skipped_old} old jobs for '{query}'")
    return jobs


def create_driver():
    """Set up and return (driver, wait, cutoff). Caller is responsible for driver.quit()."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
    # Nvoids posts in IST (UTC+5:30); compute cutoff in IST to match posted_at
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    cutoff = now_ist - timedelta(hours=config.MAX_JOB_AGE_HOURS)
    print("Opening Nvoid site...")
    return driver, wait, cutoff


def scrape_query(driver, wait, query, seen, cutoff):
    """Scrape a single query and return its jobs."""
    try:
        jobs = _search_query(driver, wait, query, seen, cutoff)
        print(f"Found {len(jobs)} recent jobs for '{query}'")
        return jobs
    except Exception as e:
        print(f"Error scraping query '{query}': {e}")
        return []
