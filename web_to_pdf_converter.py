import asyncio
import time
import os
from pathlib import Path
from playwright.async_api import async_playwright
from PyPDF2 import PdfMerger

# --- CONFIGURATION ---
# The list of URLs to download. The final merged PDF will contain these pages
# in the order they appear in this list.
URLS_TO_DOWNLOAD = [
    "https://www.google.com/",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://example.com/",
]

# Directory where the intermediate and final PDF files will be stored.
DOWNLOAD_DIRECTORY = Path("downloaded_pdfs")
# Name for the combined PDF file.
MERGED_FILENAME = "combined_report.pdf"
# --- END CONFIGURATION ---

async def download_page_as_pdf(url: str, filepath: Path):
    """
    Launches a headless browser (Chromium) to navigate to the URL and save it as a PDF.
    """
    print(f"-> Starting download for: {url}")
    
    # Use Playwright's async API for non-blocking operations
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Step 1: Perform GET request and wait 1 second (as requested)
        # The goto() method performs the request and waits for the page to load.
        await page.goto(url)
        print("   Pausing for 1 second...")
        time.sleep(1) # The required pause

        # Step 2: Save the fully rendered page as PDF
        # format='A4' ensures consistent sizing for merging
        await page.pdf(path=str(filepath), format='A4')
        print(f"   Successfully saved to: {filepath.name}")
        await browser.close()
        return filepath

def merge_pdfs_by_creation_time(directory: Path, output_filename: str):
    """
    Merges all PDF files in the specified directory, ordered by their creation time.
    """
    # 1. Find all PDF files in the directory
    pdf_files = sorted(
        directory.glob("*.pdf"),
        key=lambda f: os.path.getctime(f) # Sort by creation time (c-time)
    )

    if not pdf_files:
        print("\nNo PDFs found to merge.")
        return

    # 2. Initialize the PDF merger
    merger = PdfMerger()

    # 3. Add files to the merger
    print(f"\nMerging {len(pdf_files)} files into {output_filename}...")
    for pdf in pdf_files:
        print(f"   Adding: {pdf.name}")
        try:
            merger.append(str(pdf))
        except Exception as e:
            print(f"   [ERROR] Could not merge {pdf.name}: {e}")

    # 4. Write the merged PDF
    output_path = directory / output_filename
    with open(output_path, "wb") as f:
        merger.write(f)
    
    merger.close()
    print(f"\n✅ Merging completed. Final file saved at: {output_path.resolve()}")

async def main():
    """
    Main execution function.
    """
    print("--- WEB-TO-PDF DOWNLOADER AND MERGER ---")
    
    # 1. Setup the download directory
    DOWNLOAD_DIRECTORY.mkdir(exist_ok=True)
    print(f"Download directory prepared: {DOWNLOAD_DIRECTORY.resolve()}")
    
    downloaded_paths = []
    
    # 2. Iterate through URLs and download each one
    for i, url in enumerate(URLS_TO_DOWNLOAD):
        # Create a unique filename based on index
        filename = f"page_{i+1}.pdf"
        filepath = DOWNLOAD_DIRECTORY / filename
        
        try:
            # Pass the URL and the desired output path
            path = await download_page_as_pdf(url, filepath)
            downloaded_paths.append(path)
        except Exception as e:
            print(f"[CRITICAL ERROR] Failed to download {url}: {e}")
            
    # 3. Merge the downloaded PDFs
    if len(downloaded_paths) > 1:
        merge_pdfs_by_creation_time(DOWNLOAD_DIRECTORY, MERGED_FILENAME)
    elif len(downloaded_paths) == 1:
        print(f"\nOnly one PDF was downloaded. No merging required: {downloaded_paths[0].name}")
    else:
        print("\nNo files were successfully downloaded.")
    
    print("--- PROCESS COMPLETE ---")


if __name__ == "__main__":
    # Playwright requires an asynchronous runtime
    asyncio.run(main())
