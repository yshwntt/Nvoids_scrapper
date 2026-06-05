from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import config


def _parse_posted_time(time_str):
    """Parse time string like '01:27 AM 06-Jun-26' into datetime."""
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p %d-%b-%y")
    except Exception:
        return None


def _search_query(driver, wait, query, seen, cutoff):
    """Search one query and return new jobs posted within cutoff time."""
    driver.get("https://www.nvoids.com/index.jsp")
    time.sleep(1)

    driver.execute_script("""
        var frames = document.querySelectorAll("iframe");
        frames.forEach(f => { try { f.remove(); } catch(e) {} });
    """)

    search_box = wait.until(EC.element_to_be_clickable((By.ID, "search_id")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_box)
    time.sleep(config.SEARCH_DELAY)

    search_box.clear()
    time.sleep(0.5)
    search_box.send_keys(query)
    print(f"Typed query: {query}")
    time.sleep(config.SEARCH_DELAY)

    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", submit_btn)
    print("Clicked Submit")
    time.sleep(4)

    # Each job is a <tr> with: title link | location | time
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

            # Extract time from last <td> in the row
            cells = row.find_elements(By.TAG_NAME, "td")
            posted_at = None
            if cells:
                time_text = cells[-1].text.strip()
                posted_at = _parse_posted_time(time_text)

            # Filter by cutoff time (IST — same timezone as datetime.now())
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


def scrape_jobs(queries=None):
    """Scrape job listings from Nvoids for all queries."""
    if queries is None:
        queries = config.SEARCH_QUERIES
    if isinstance(queries, str):
        queries = [queries]

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)

    print("Opening Nvoid site...")

    cutoff = datetime.now() - timedelta(hours=config.MAX_JOB_AGE_HOURS)

    all_jobs = []
    seen = set()

    try:
        for query in queries:
            try:
                jobs = _search_query(driver, wait, query, seen, cutoff)
                print(f"Found {len(jobs)} recent jobs for '{query}'")
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error scraping query '{query}': {e}")

        print(f"Total unique recent jobs: {len(all_jobs)}")
        return driver, all_jobs

    except Exception as e:
        print(f"Error scraping jobs: {e}")
        driver.quit()
        raise
