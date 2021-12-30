import uuid
import logging
from dataclasses import field, dataclass
from enum import Enum
from typing import Any, Type
import time
import requests

from .config import Config

__all__ = ["TranscriptionStatus", "TranscriptionJob"]


class TranscriptionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@dataclass
class TranscriptionJob:
    job_uri: str
    config: Config

    media_format: str = "mp3"
    job_name: str = field(default_factory=lambda: str(uuid.uuid4()))
    started: bool = False

    def start(self):
        self.config.transcription.start_transcription_job(
            TranscriptionJobName=self.job_name,
            Media={"MediaFileUri": self.job_uri},
            MediaFormat=self.media_format,
            Settings={
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": 2,
            },
            LanguageCode="en-US",
        )

        self.started = True

    @classmethod
    def from_existing_job(
        cls, config: Config, job_name: str
    ) -> Type["TranscriptionJob"]:
        job = cls(job_uri="", config=config)
        job.job_name = job_name
        job.started = True

        return job

    @property
    def status(self) -> TranscriptionStatus:
        assert self.started
        job = self.config.transcription.get_transcription_job(
            TranscriptionJobName=self.job_name
        )
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        return TranscriptionStatus(job_status)

    def block_on_transcript(self) -> Any:
        while True:
            logging.info(f"Polling transcription job for {self.job_uri}")
            status = self.status
            if status == TranscriptionStatus.FAILED:
                logging.error(
                    f"Could not complete transcription job for {self.job_uri}."
                )
                raise ValueError("Could not complete transcription.")
            elif status == TranscriptionStatus.COMPLETED:
                job = self.config.transcription.get_transcription_job(
                    TranscriptionJobName=self.job_name
                )
                transcript_uri = job["TranscriptionJob"]["Transcript"][
                    "TranscriptFileUri"
                ]
                return self.fetch_transcript(transcript_uri)

            time.sleep(3.0)

    @staticmethod
    def fetch_transcript(transcript_uri) -> Any:
        response = requests.get(transcript_uri)
        if response.status_code != 200:
            logging.error("Failed to fetch finished transcript.")
            return None

        return response.json()
