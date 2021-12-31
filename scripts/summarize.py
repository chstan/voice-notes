"""Provides a summary of the status of all managed voice notes.

Only voice notes which have not been synchronized all the way to Notion are 
shown with their name. This allows easily finding items which ran into an error
someplace for debugging.
"""
from collections import Counter

from voice_notes import global_config
from voice_notes.voice_note import VoiceNoteStatus

if __name__ == "__main__":
    with global_config.db() as db:
        items = dict(db).values()

    items_by_status = Counter([item.status for item in items])

    for k, v in sorted(items_by_status.items(), key=lambda x: x[0]):
        print(f"{k.name}: {v} item(s)")

        if k != VoiceNoteStatus.Notion and v > 0:
            all_items_with_status = [item for item in items if item.status == k]
            for item in all_items_with_status:
                print(f" - {item.name}")
