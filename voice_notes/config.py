import os
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager

import boto3
import botocore.config
import shelve
from typing import Any
from notion_client import Client

__all__ = ["INGRESS_PATH", "ARCHIVE_PATH", "config", "Config"]

ROOT_PATH = Path.home() / ".voice-note"
INGRESS_PATH = ROOT_PATH / "ingress"
DB_PATH = ROOT_PATH / "archive" / "notes"
SECRETS_PATH = ROOT_PATH / "secrets"
ARCHIVE_PATH = ROOT_PATH / "archive" / "mp3s"


@dataclass
class Config:
    s3: Any = field(init=False)
    transcription: Any = field(init=False)
    voice_bucket: Any = field(init=False)
    _notion_client: Client = None

    boto_config: botocore.config.Config = field(init=False)
    boto_session: Any = field(init=False)

    aws_region = "us-west-2"
    aws_profile_name: str = "voice-transcription-user"
    bucket_name: str = "voice-transcription-notes"

    @staticmethod
    def inject_secrets():
        """Cheap environment variables without dependencies."""
        for p in SECRETS_PATH.glob("*.secret.env"):
            with open(str(p.absolute())) as secret_f:
                for line in secret_f.readlines():
                    try:
                        splits = line.split("=")
                        k, v = splits[0], "=".join(splits[1:])
                        os.environ[k] = v
                    except ValueError:
                        pass

    @property
    def notion_client(self) -> Client:
        if not self._notion_client:
            self._notion_client = Client(auth=os.environ["NOTION_TOKEN"])

        return self._notion_client

    def __post_init__(self):
        self.inject_secrets()

        INGRESS_PATH.mkdir(exist_ok=True, parents=True)
        ARCHIVE_PATH.mkdir(exist_ok=True, parents=True)

        self.boto_config = botocore.config.Config(
            region_name=self.aws_region,
        )
        self.boto_session = boto3.Session(profile_name=self.aws_profile_name)

        # Set up clients
        self.s3 = self.boto_session.resource("s3")
        self.transcription = self.boto_session.client("transcribe")

        # Set up resources
        self.voice_bucket = self.s3.Bucket(self.bucket_name)

    @contextmanager
    def db(self):
        with shelve.open(str(DB_PATH.absolute())) as db:
            yield db

    def get_by_name(self, name):
        with self.db() as db:
            return db[name]


config = Config()
