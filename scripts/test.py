"""This is just for testing ideas and ensuring methods work interactively."""
import argparse
from voice_notes import global_config, VoiceNote

notion = global_config.notion_client

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
    print(item.date)
