import os
import time
import subprocess
import sys
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1. Definer sti til output
user_home = os.path.expanduser("~")
output_dir = os.path.join(user_home, "M:\\mp3", "i")
os.makedirs(output_dir, exist_ok=True)
csv_filepath = os.path.join(output_dir, "playlist_sange.csv")

playlist_url = "https://open.spotify.com/track/4P3QwRdqTV274oXEZ5jK2f"  # Kunstner/playlist-URL
https_socket = playlist_url  # Bruger bare standard URL'en til spotdl
if not playlist_url.startswith("https://"):
    print("Fejl: URL'en skal starte med 'https://'.")
    sys.exit(1)

# 2. Opsæt Firefox (Selenium Manager klarer driveren automatisk)
options = Options()
# options.add_argument("--headless")  # Fjern '#' hvis browseren skal køre skjult i baggrunden

driver = webdriver.Firefox(options=options)

try:
    print(f"Åbner Spotify: {playlist_url}")
    driver.get(playlist_url)
    https_socket = playlist_url  # Gemmer URL'en til senere brug i spotdl

    # 3. Vent på at sporene bliver synlige
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/track/")]')))

    # 4. Rul ned for at indlæse alle sange i playlisten (lazy-loading)
    print("Ruller ned for at hente alle sange...")
    for _ in range(12):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(0.5)

    # 5. Send HTML-koden videre til BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    track_links = soup.find_all("a", href=lambda h: h and "/track/" in h)

    scraped_songs = []
    seen_titles = set()

    for link in track_links:
        title = link.get_text(strip=True)
        
        if not title or title in seen_titles:
            continue
        
        seen_titles.add(title)
        row = link.find_parent("div", {"role": "row"}) or link.find_parent("div", class_=lambda c: c and "row" in c.lower())

        artists = "Ukendt kunstner"
        album = "N/A"

        if row:
            # Udtræk kunstnere
            artist_elems = row.find_all("a", href=lambda h: h and "/artist/" in h)
            if artist_elems:
                artists = ", ".join([a.get_text(strip=True) for a in artist_elems])

            # Udtræk album
            album_elem = row.find("a", href=lambda h: h and "/album/" in h)
            if album_elem:
                album = album_elem.get_text(strip=True)

        scraped_songs.append({
            "#": len(scraped_songs) + 1,
            "Titel": title,
            "Kunstner": artists,
            "Album": album
        })

    # 6. Gem data i en CSV-fil
    df = pd.DataFrame(scraped_songs)
    df.to_csv(csv_filepath, index=False, encoding="utf-8-sig")

    print(f"\nSucces! Gemte metadata for {len(df)} sange i:")
    print(csv_filepath)

finally:
    driver.quit()

# 7. Download MP3-filer via spotdl og sorter i album-mapper
print("\nStarter download af MP3-filer via spotdl...")

python_executable = sys.executable

# Rettet: Fjernet bindestreg og samlet på én gyldig linje
output_template = os.path.join(output_dir, "{album}", "{artist} - {title}.{output-ext}")

command = [
    python_executable,
    "-m",
    "spotdl",
    https_socket,
    "--output", output_template,
    "--format", "mp3",
    "--bitrate", "320k",
    "--overwrite", "skip"
]

subprocess.run(command)

print(f"\nAlt er fuldført! MP3-filer og mapper er klar i: {output_dir}")