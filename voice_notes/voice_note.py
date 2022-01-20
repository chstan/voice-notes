"""Models the ETL pipeline for voice notes."""
import warnings
import datetime
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import shutil
from typing import Any, Callable, Optional
import functools

import logging
from botocore.exceptions import ClientError
from voice_notes.notion.basics import RichText, Block
from voice_notes.notion.search import get_daily_page_id

from voice_notes.transcript import FormattingSettings, NoSpeakersException, Transcript

from .transcription import TranscriptionJob
from .config import Config, INGRESS_PATH, ARCHIVE_PATH

__all__ = ["VoiceNote", "VoiceNoteStatus"]


class VoiceNoteStatus(int, Enum):
    """Enumerates data transform/ETL stages for voice note transcription."""

    Ingress = 0  # Waiting for processing
    Local = 10  # Saved in on disk archive only
    S3 = 20  # Saved on S3
    Transcribed = 30  # Finished AWS Transcribe job
    Notion = 40  # Formatted and synchronized to Notion
    Evicted = 50  # Item has no speech or was removed by user


def bump_status(status: VoiceNoteStatus):
    """Conveniently set the status attribute after successful completion of an ETL step."""

    def inner_decorator(f: Callable):
        @functools.wraps(f)
        def wrapped_f(self, config: Config, *args):
            if f(self, config, *args):
                self.status = status
                config.save(self)

        return wrapped_f

    return inner_decorator


@dataclass
class VoiceNote:
    """Models the ETL pipeline for audio voice notes from S3, through transcription, to Notion embedding."""

    path: Path
    status: VoiceNoteStatus = VoiceNoteStatus.Ingress
    transcript: Any = field(default=None, repr=False)

    @property
    def ingress_relative_path(self) -> Optional[Path]:
        """Determine the path for the associated media file relative the ingress location."""
        # a sanity check in order to ensure that we don't
        assert "mp3" in self.name
        try:
            return self.path.relative_to(INGRESS_PATH)
        except ValueError:
            return None

    @property
    def name(self) -> str:
        """Fetch the name from the filename of the original media."""
        return self.path.name

    def safe_synchronize(self, config: Config):
        """Log errors from synchronization."""
        try:
            self.synchronize(config)
        except Exception as e:
            logging.error(f"Unhandled exception: {e}.")

    def synchronize(self, config: Config):
        """Run the full ETL pipeline for an voice note as MP3."""
        self.cache_local(config)
        self.upload_to_s3(config)
        self.transcribe_on_s3(config)
        self.add_to_notion(config)

    @bump_status(VoiceNoteStatus.Local)
    def cache_local(self, config: Config):
        """Move the file out of the ingress location into the archive and sets up DB tracking."""
        if self.status != VoiceNoteStatus.Ingress:
            return

        rel_path = self.ingress_relative_path
        assert rel_path is not None

        new_path = ARCHIVE_PATH / rel_path
        if new_path.exists():
            warnings.warn(
                "File is already imported. Skipping and removing ingress file."
            )
            os.remove(str((INGRESS_PATH / rel_path).absolute()))
            return

        shutil.move(self.path, new_path)
        self.path = new_path
        return True

    @bump_status(VoiceNoteStatus.S3)
    def upload_to_s3(self, config: Config):
        """Ensure that the file is uploaded to S3 for retention."""
        if self.status != VoiceNoteStatus.Local:
            return

        object_name = self.name
        logging.info(f"Uploading file {self.path} as {object_name} to S3.")
        try:
            config.s3.meta.client.upload_file(
                str(self.path.absolute()), config.voice_bucket.name, object_name
            )
        except ClientError as e:
            logging.error(e)

        return True

    @bump_status(VoiceNoteStatus.Transcribed)
    def transcribe_on_s3(self, config: Config):
        """Run transcription for this media file on S3."""
        if self.status != VoiceNoteStatus.S3:
            return

        job_uri = f"s3://{config.voice_bucket.name}/{self.name}"

        logging.info(f"Running transcription job for {job_uri}")
        job = TranscriptionJob(job_uri=job_uri, config=config)
        job.start()

        transcript = job.block_on_transcript()
        if transcript is None:
            return

        logging.info(f"Successfully retrieved transcript")
        self.transcript = transcript
        return True

    @bump_status(VoiceNoteStatus.Transcribed)
    def attach_existing_transcript(self, config: Config, job_name: str):
        """Attach and import a transcript from a previous AWS Transcribe `job_name`."""
        assert self.status == VoiceNoteStatus.S3

        job = TranscriptionJob.from_existing_job(config, job_name)
        transcript = job.block_on_transcript()
        if transcript is None:
            return

        self.transcript = transcript
        return True

    @bump_status(VoiceNoteStatus.S3)
    def reset_transcript(self, config: Config):
        """Reset the stage of this note back to before transcription happened.

        This was used a few times while tweaking the AWS Transcribe settings for good results.
        """
        assert self.status > VoiceNoteStatus.S3

        self.transcript = None
        return True

    def to_block(self, file=True):
        """Convert this voice note to a Notion block object with S3 link."""
        assert self.status >= VoiceNoteStatus.Transcribed

        settings = FormattingSettings()
        t = Transcript.from_aws_transcribe_json(
            self.transcript["results"],
            settings=settings,
        )
        if len(t.items_by_speaker()) > 95:
            logging.warn("Concatenating speakers!")
            settings = FormattingSettings(break_speakers=False)
            t = Transcript.from_aws_transcribe_json(
                self.transcript["results"],
                settings=settings,
            )

        block = t.to_block(RichText.bold(self.name))

        if file:
            Block.prepend_child(
                block,
                Block.href(
                    f"{os.environ['AWS_SLUG']}{self.name}", f"AWS Console: {self.name}"
                ),
            )

        return block

    @bump_status(VoiceNoteStatus.Notion)
    def add_to_notion(self, config: Config):
        """Synchronize the voice note to the appropriate Notion planning page."""
        if self.status >= VoiceNoteStatus.Notion:
            return

        page_id = get_daily_page_id(config.notion_client, self.date)

        try:
            block_children = self.to_block()
        except NoSpeakersException:
            self.status = VoiceNoteStatus.Evicted
            config.save(self)
            return

        config.notion_client.blocks.children.append(
            block_id=page_id,
            children=[block_children],
        )

        return True

    @property
    def date(self) -> datetime.datetime:
        """Determine the date for the voice note from the filename."""
        date = self.name.split("_")[0]
        year = int(f"20{date[:2]}")
        month = int(date[2:4])
        day = int(date[4:])
        return datetime.datetime(year=year, month=month, day=day, hour=12)
