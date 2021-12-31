"""Import all of the voice notes in the ingress folder."""
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from tqdm import tqdm
from voice_notes import VoiceNote, INGRESS_PATH, global_config


if __name__ == "__main__":
    # sort here so that we get notes in the order they were created when they get
    # added to Notion
    for_import = sorted(list(INGRESS_PATH.glob("*.mp3")), key=lambda p: p.stem)

    logging.info("Checking for new items...")
    for item in tqdm(for_import):
        vnote = VoiceNote(item)
        vnote.synchronize(global_config)

    logging.info("Checking to see if previously imported need processing...")
    with global_config.db() as db:
        items = sorted(list(dict(db).values()), key=lambda item: item.name)

    for item in tqdm(items):
        try:
            item.synchronize(global_config)
        except Exception as e:
            logging.error(f"Unhandled exception: {e}. Continuing.")
            continue
