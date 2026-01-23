# file: nist_sp80053_watcher.py
import os, time, hashlib, json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SP80053_URL = "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"  # keep in config
DATA_DIR = Path("data/")
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "state.json"

def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_seen_checksum": None, "last_seen_href": None}

def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def fetch_latest_pdf():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=opts)
    driver.get(SP80053_URL)

    # Example selectors – adjust after inspecting the page once:
    # Look for the main “Download PDF”/“View PDF” link in the page
    link_els = driver.find_elements(By.CSS_SELECTOR, "a")
    pdf_links = [a.get_attribute("href") for a in link_els if a.get_attribute("href") and a.get_attribute("href").lower().endswith(".pdf")]

    driver.quit()

    if not pdf_links:
        raise RuntimeError("Could not find any PDF links on page.")
    # Heuristic: choose the first PDF (or the one with 'SP 800-53' in name)
    pdf_url = next((x for x in pdf_links if "800-53" in x), pdf_links[0])

    # Download with requests (faster than Selenium)
    import requests
    r = requests.get(pdf_url, timeout=60)
    r.raise_for_status()
    pdf_bytes = r.content
    return pdf_url, pdf_bytes

def main():
    state = _load_state()
    pdf_url, pdf_bytes = fetch_latest_pdf()
    current_checksum = _sha256_bytes(pdf_bytes)

    if current_checksum != state.get("last_seen_checksum"):
        # New/updated PDF detected
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_pdf = DATA_DIR / f"SP800-53_{ts}.pdf"
        out_pdf.write_bytes(pdf_bytes)
        print(f"[+] New SP 800-53 PDF saved: {out_pdf.name}")

        state["last_seen_checksum"] = current_checksum
        state["last_seen_href"] = pdf_url
        _save_state(state)
        return str(out_pdf)  # path to new file
    else:
        print("[=] No change detected.")
        return None

if __name__ == "__main__":
    main()
