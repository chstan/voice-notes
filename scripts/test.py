import argparse
from voice_notes import global_config, Transcript, VoiceNote
from voice_notes.notion.search import get_page_matching_exact_title

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

# list_users_response = notion.users.list()
# pprint(list_users_response)

# notion.blocks.children.append(
#    block_id=personal_journal_page.id,
#    children=[
#        Block.child_page("child_page_test"),
#    ]
# )
