#!/usr/bin/env python3
"""
Screenshot capture script for Spell UI test artifacts
"""

import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Setup Chrome driver with proper options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)

def capture_screenshot(driver, url, output_name):
    """Capture screenshot of a specific URL"""
    print(f"Capturing: {output_name}")
    driver.get(url)
    time.sleep(2)  # Wait for page to fully render
    
    # Get screenshot
    screenshot_path = f"test-artifacts/screenshots/{output_name}"
    driver.save_screenshot(screenshot_path)
    print(f"  ✅ Saved to {screenshot_path}")
    return screenshot_path

def main():
    # Create screenshots directory
    os.makedirs('test-artifacts/screenshots', exist_ok=True)
    
    # Get absolute path to test artifacts
    base_path = Path(__file__).parent.absolute()
    
    # Test files to capture
    test_files = [
        ('home-with-google-icons.html', 'home-screen.png'),
        ('processing-with-google-icons.html', 'processing-screen.png'),
        ('processing-hitl-left-bottom.html', 'processing-hitl.png'),
        ('processing-with-preview.html', 'processing-preview.png'),
    ]
    
    # Setup driver
    driver = setup_driver()
    
    try:
        print("=== Spell UI Screenshot Capture ===\n")
        
        for filename, output_name in test_files:
            file_url = f"file://{base_path}/test-artifacts/{filename}"
            if os.path.exists(f"{base_path}/test-artifacts/{filename}"):
                capture_screenshot(driver, file_url, output_name)
            else:
                print(f"  ❌ File not found: {filename}")
        
        print("\n=== Screenshot Capture Complete ===")
        print("All screenshots saved to: test-artifacts/screenshots/")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()