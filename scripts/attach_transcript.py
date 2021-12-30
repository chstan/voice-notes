import argparse
from voice_notes import global_config, VoiceNote

parser = argparse.ArgumentParser("Attach an existing transcript job.")
parser.add_argument(
    "--file",
    type=str,
    required=True,
    help="The filename and extension (DB key) for the audio note.",
)
parser.add_argument(
    "--job", type=str, required=True, help="The ID used for the transcription job."
)


if __name__ == "__main__":
    args = parser.parse_args()

    item: VoiceNote = global_config.get_by_name(args.file)
    item.attach_existing_transcript(global_config, args.job)
    print(item)
