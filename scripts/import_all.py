import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from tqdm import tqdm
from voice_notes import VoiceNote, INGRESS_PATH, global_config


if __name__ == "__main__":
    for_import = INGRESS_PATH.glob("*.mp3")

    logging.info("Checking for new items...")
    for item in tqdm(for_import):
        vnote = VoiceNote(item)
        vnote.synchronize(global_config)

    logging.info("Checking to see if previously imported need processing...")
    with global_config.db() as db:
        items = dict(db).values()

    for item in tqdm(items):
        try:
            item.synchronize(global_config)
        except Exception as e:
            logging.error(f"Unhandled exception: {e}. Continuing.")
            continue

