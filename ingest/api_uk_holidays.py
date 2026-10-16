"""Fetch and save UK bank holiday data."""

import json
from datetime import datetime
from pathlib import Path

import requests


CURRENT_YEAR = datetime.now().year
BANK_HOLIDAYS_URL = "https://www.gov.uk/bank-holidays.json"
BANK_HOLIDAYS_PATH = Path("data/uk_bank_holidays") / f"{CURRENT_YEAR}.json"


def main() -> None:
    """Fetch and persist the current year's UK bank holiday data."""
    try:
        response = requests.get(BANK_HOLIDAYS_URL, timeout=30)
        response.raise_for_status()
        bank_holidays = response.json()
    except requests.exceptions.RequestException as error:
        raise RuntimeError("Failed to fetch UK bank holiday data.") from error

    BANK_HOLIDAYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BANK_HOLIDAYS_PATH.write_text(
        json.dumps(bank_holidays, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved UK bank holiday data to {BANK_HOLIDAYS_PATH}")


if __name__ == "__main__":
    main()
