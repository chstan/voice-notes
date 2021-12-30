import argparse
from enum import Enum
from voice_notes import global_config, VoiceNote, Transcript

class ItemAction(str, Enum):
    Info = "info"
    Delete = "delete"
    ResetTranscript = "reset-transcript"

    def __str__(self) -> str:
        return self.value

parser = argparse.ArgumentParser("Print information about a note")
parser.add_argument(
    "--file",
    type=str,
    required=True,
    help="The filename and extension (DB key) for the audio note.",
)
parser.add_argument('--action', type=ItemAction, choices=list(ItemAction), required=True, help="Which action to take for the specified file.")


if __name__ == "__main__":
    args = parser.parse_args()

    item: VoiceNote = global_config.get_by_name(args.file)

    if args.action == ItemAction.Info:
        transcript = Transcript.from_aws_transcribe_json(item.transcript["results"])
        print(transcript.to_string())
    elif args.action == ItemAction.Delete:
        with global_config.db() as db:
            del db[args.file]
    elif args.action == ItemAction.ResetTranscript:
        item.reset_transcript(global_config)
