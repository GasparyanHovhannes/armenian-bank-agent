import json
import os

GARBAGE_PHRASES = [
    "You need to enable JavaScript",
    "Գլխավոր էջ",
    "404 Error",
    "ChatBot",
    "ACBA Leasing is the first registered",
    "Federation settlement card",
    "utility payments Depositing funds",
    "SMS notification service OTHER RISKS",
    "Visa Signature card allows you to get travel insurance",
    "USSD service SMS notification",
    "Credit card lines Card loss",
]

MIN_CHUNK_LENGTH = 100  # characters


def is_useful(chunk: dict) -> bool:
    text = chunk.get("text", "")
    if len(text) < MIN_CHUNK_LENGTH:
        return False
    for phrase in GARBAGE_PHRASES:
        if phrase in text:
            return False
    return True


def merge():
    # Load scraped data
    scraped_path = "data/scraped/acba_bank.json"
    manual_path = "data/manual/all_banks.json"
    output_path = "data/merged/all_banks.json"

    os.makedirs("data/merged", exist_ok=True)

    scraped = []
    if os.path.exists(scraped_path):
        with open(scraped_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        scraped = [c for c in raw if is_useful(c)]
        print(f"Scraped ACBA: {len(raw)} total, {len(scraped)} after filtering")

    manual = []
    if os.path.exists(manual_path):
        with open(manual_path, "r", encoding="utf-8") as f:
            manual = json.load(f)
        print(f"Manual data: {len(manual)} chunks")

    merged = manual + scraped
    print(f"Total merged: {len(merged)} chunks")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    merge()