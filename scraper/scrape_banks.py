import requests
from bs4 import BeautifulSoup
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

BANKS = {
    "Ameriabank": {
        "credits": [
            "https://ameriabank.am/en/personal/loans/consumer-loans/consumer-loans",
            "https://ameriabank.am/en/personal/loans/consumer-loans/overdraft",
            "https://ameriabank.am/en/personal/loans/consumer-loans/credit-line",
            "https://ameriabank.am/en/personal/loans/mortgage",
            "https://ameriabank.am/en/personal/loans/car-loans",
        ],
        "deposits": [
            "https://ameriabank.am/en/personal/deposits/term-deposit",
            "https://ameriabank.am/en/personal/deposits/demand-deposit",
            "https://ameriabank.am/en/personal/deposits/savings-account",
        ],
        "branches": [
            "https://ameriabank.am/en/service-network",
        ],
    },
    "Ardshinbank": {
        "credits": [
            "https://www.ardshinbank.am/en/loans",
            "https://www.ardshinbank.am/en/mortgage",
            "https://www.ardshinbank.am/en/consumer-loan",
        ],
        "deposits": [
            "https://www.ardshinbank.am/en/deposits",
            "https://www.ardshinbank.am/en/savings",
        ],
        "branches": [
            "https://www.ardshinbank.am/en/branches",
            "https://www.ardshinbank.am/en/contacts",
        ],
    },
    "ACBA Bank": {
        "credits": [
            "https://www.acba.am/en/individuals/loans/collateral-loans/deposit-secured",
            "https://www.acba.am/en/individuals/loans",
        ],
        "deposits": [
            "https://www.acba.am/en/individuals/save-and-invest/deposits/classic",
            "https://www.acba.am/en/individuals/save-and-invest/deposits/accumulative",
            "https://www.acba.am/en/individuals/save-and-invest/deposits/family",
        ],
        "branches": [
            "https://www.acba.am/en/about-bank/Branches-and-ATMs",
            "https://www.acba.am/en/contacts",
        ],
    },
}

from seleniumbase import Driver

def make_driver():
    """Create a headless Chrome browser — auto-matches ChromeDriver version."""
    driver = Driver(browser="chrome", headless=True)
    return driver


def scrape_page(driver, url: str) -> str:
    """Fetch a URL using Selenium and return clean text."""
    try:
        driver.get(url)
        # Wait up to 10 seconds for the body to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(4)  # extra wait for JS to finish rendering

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Remove noise
        for tag in soup(["nav", "footer", "script", "style",
                          "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        print(f"  WARNING: Could not scrape {url} — {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def scrape_all_banks(output_dir: str = "data/scraped"):
    os.makedirs(output_dir, exist_ok=True)
    all_chunks = []

    print("Starting headless Chrome browser...")
    driver = make_driver()

    try:
        for bank_name, topics in BANKS.items():
            print(f"\nScraping {bank_name}...")
            bank_chunks = []

            for topic, urls in topics.items():
                print(f"  Topic: {topic}")
                for url in urls:
                    print(f"    Fetching: {url}")
                    text = scrape_page(driver, url)

                    if not text:
                        continue

                    chunks = chunk_text(text)
                    for chunk in chunks:
                        bank_chunks.append({
                            "bank": bank_name,
                            "topic": topic,
                            "url": url,
                            "text": chunk,
                        })

                    print(f"    Got {len(chunks)} chunks")
                    time.sleep(4)

            out_path = os.path.join(
                output_dir,
                f"{bank_name.lower().replace(' ', '_')}.json"
            )
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(bank_chunks, f, ensure_ascii=False, indent=2)

            print(f"  Saved {len(bank_chunks)} chunks to {out_path}")
            all_chunks.extend(bank_chunks)

    finally:
        driver.quit()  # always close the browser

    combined_path = os.path.join(output_dir, "all_banks.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Total chunks: {len(all_chunks)}")
    print(f"Combined file: {combined_path}")
    return all_chunks


if __name__ == "__main__":
    scrape_all_banks()