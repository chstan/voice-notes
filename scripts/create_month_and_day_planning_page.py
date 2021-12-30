import datetime
import argparse

from voice_notes import global_config
from voice_notes.notion.template_journal_page import get_or_create_daily_page_id

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--day_delta", type=int, default=0)

notion = global_config.notion_client

if __name__ == "__main__":
    args = parser.parse_args()
    delta = datetime.timedelta(days=args.day_delta)
    daily_id = get_or_create_daily_page_id(notion, datetime.datetime.now() + delta)
