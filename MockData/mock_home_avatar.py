# -*- coding: utf-8 -*-
"""
GrowQuest Tower – HomePage avatar mocker (via localStorage)
- Opens your HomePage (served by XAMPP)
- Sets localStorage.lastScanSummary / summaryVisible / lightIsOn
- Optionally cycles presets forever until Ctrl+C
"""

import json
import time
import random
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# --------- Preset builders (match your JS structure) ---------
STAGES = ["Seedling", "Growing", "Mature", "Harvest"]

def mk_section(idx, has, stage, pct):
    return {
        "index": idx + 1,
        "has_plant": bool(has),
        "stage": stage,
        "green_pct": int(pct),
        "image": f"sec_{idx+1}.jpg"
    }

def mk_summary(sections, scan_dir="scan/dev"):
    count = len(sections)
    avg = round(sum(int(s.get("green_pct", 0) or 0) for s in sections) / count) if count else 0
    return {
        "scan_dir": scan_dir,
        "count": count,
        "avg_green_pct": avg,
        "sections": sections
    }

def preset_empty():
    return mk_summary([mk_section(i, False, "Seedling", 0) for i in range(6)])

def preset_seedlings():
    pcts = [3, 4, 6, 7, 5, 8]
    return mk_summary([mk_section(i, True, "Seedling", pcts[i]) for i in range(6)])

def preset_mixed():
    return mk_summary([
        mk_section(0, True,  "Seedling", 4),
        mk_section(1, True,  "Growing", 12),
        mk_section(2, True,  "Growing", 15),
        mk_section(3, True,  "Mature",  21),
        mk_section(4, False, "Seedling", 0),
        mk_section(5, True,  "Harvest", 28),
    ])

def preset_mature():
    pcts = [22, 24, 23, 31, 25, 29]
    stages = ["Mature","Harvest","Mature","Harvest","Mature","Harvest"]
    return mk_summary([mk_section(i, True, stages[i], pcts[i]) for i in range(6)])

def preset_random():
    secs = []
    for i in range(6):
        has = random.random() > 0.15
        stg = random.choice(STAGES)
        if stg == "Seedling":
            pct = random.randint(0, 8)
        elif stg == "Growing":
            pct = 8 + random.randint(0, 10)
        elif stg == "Mature":
            pct = 18 + random.randint(0, 10)
        else:  # Harvest
            pct = 26 + random.randint(0, 10)
        secs.append(mk_section(i, has, stg, pct if has else 0))
    return mk_summary(secs)

PRESETS = {
    "empty": preset_empty,
    "seedlings": preset_seedlings,
    "mixed": preset_mixed,
    "mature": preset_mature,
    "random": preset_random,
}

# --------- Selenium helpers ---------
def apply_summary(driver, summary, show_panel=True, light_on=True):
    """
    Inject summary into localStorage and refresh/trigger on-page functions.
    """
    js = r"""
    (function(summary, showPanel, lightOn){
      try {
        localStorage.setItem('lastScanSummary', JSON.stringify(summary));
        localStorage.setItem('summaryVisible', showPanel ? 'true' : 'false');
        localStorage.setItem('lightIsOn', lightOn ? 'true' : 'false');

        // If HomePage exposes helpers, update live without reload
        if (window.__mocking && typeof window.__mocking.updatePotGridFromSummary === 'function') {
          window.__mocking.updatePotGridFromSummary(summary);
          if (window.__mocking.renderScanSummary) {
            window.__mocking.renderScanSummary(summary, showPanel);
          }
          return 'live';
        } else {
          // Otherwise refresh to let page read localStorage on load
          location.reload();
          return 'reloaded';
        }
      } catch(e){
        return 'error:' + e.message;
      }
    })(arguments[0], arguments[1], arguments[2]);
    """
    result = driver.execute_script(js, summary, bool(show_panel), bool(light_on))
    return result

def wait_until_loaded(driver, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            ready = driver.execute_script("return document.readyState")
            if ready == "complete":
                return True
        except WebDriverException:
            pass
        time.sleep(0.2)
    return False

# --------- CLI & main ---------
def main():
    ap = argparse.ArgumentParser(description="Mock HomePage avatar state via localStorage")
    ap.add_argument("--url", default="http://localhost/Senior_Project/GrowQuest-Tower/HomePage.html",
                    help="URL of HomePage.html (served by XAMPP)")
    ap.add_argument("--preset", default="mixed",
                    choices=list(PRESETS.keys()),
                    help="Preset to apply")
    ap.add_argument("--cycle", action="store_true",
                    help="Cycle presets forever until Ctrl+C")
    ap.add_argument("--interval", type=float, default=4.0,
                    help="Seconds between cycles when --cycle is set")
    ap.add_argument("--light_on", action="store_true",
                    help="Turn lightIsOn to true in localStorage")
    args = ap.parse_args()

    # Launch Chrome (Selenium Manager auto-downloads driver)
    opts = Options()
    opts.add_argument("--start-maximized")
    # Uncomment to see your usual profile instead of a fresh one:
    # opts.add_argument(r'--user-data-dir=C:\Users\YourUser\AppData\Local\Google\Chrome\User Data')

    driver = webdriver.Chrome(options=opts)
    driver.get(args.url)
    wait_until_loaded(driver)

    def apply_named(preset_name):
        summary = PRESETS[preset_name]() if preset_name in PRESETS else preset_mixed()
        result = apply_summary(driver, summary, show_panel=True, light_on=args.light_on)
        print(f"✅ Applied preset '{preset_name}' → {result} | avg_green_pct={summary['avg_green_pct']}")
        # If page reloaded, give it a moment
        if result == "reloaded":
            wait_until_loaded(driver)
        return summary

    if not args.cycle:
        apply_named(args.preset)
        print("ℹ️ Done. Close the browser or run again with --cycle to keep changing states.")
        return

    # Cycle mode
    order = ["seedlings", "mixed", "mature", "random"]
    if args.preset != "mixed":
        # Start from the chosen preset, then continue the cycle
        order = [args.preset] + [p for p in order if p != args.preset]

    print(f"🔁 Cycling presets {order} every {args.interval}s. Press Ctrl+C to stop.")
    try:
        i = 0
        while True:
            apply_named(order[i % len(order)])
            i += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        # Keep the browser open so you can inspect; comment this out to auto-close.
        pass
        # driver.quit()

if __name__ == "__main__":
    main()
