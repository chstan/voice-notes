import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

import argparse
from voice_notes import global_config, VoiceNote

parser = argparse.ArgumentParser("Attach an existing transcript job.")
parser.add_argument(
    "--file",
    type=str,
    required=True,
    help="The filename and extension (DB key) for the audio note.",
)


if __name__ == "__main__":
    args = parser.parse_args()

    item: VoiceNote = global_config.get_by_name(args.file)
    item.synchronize(global_config)
    print(item)
