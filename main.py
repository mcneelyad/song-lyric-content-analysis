from dotenv import load_dotenv
import json
import lyricsgenius
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")
genius = lyricsgenius.Genius(token)
genius.verbose = False  # Turn off status messages
genius.remove_section_headers = True  # Remove section headers like [Chorus], [Verse], etc.
genius.excluded_terms = ["(Remix)", "(Live)"]
