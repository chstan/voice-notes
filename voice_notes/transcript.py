"""Provides structured representation of audio transcripts."""
from dataclasses import dataclass, field
import datetime
import math
from typing import Any, Dict, List, Optional

from voice_notes.notion.basics import RichText, Block

__all__ = ["Transcript"]


@dataclass
class AWSTimestamped:
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def __post_init__(self):
        if self.start_time:
            self.start_time = float(self.start_time)

        if self.end_time:
            self.end_time = float(self.end_time)


@dataclass
class AWSSegment(AWSTimestamped):
    speaker_label: str = "spk_0"
    items: List[Dict[str, Any]] = field(default_factory=list)
    index: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.speaker_label = self.speaker_label.replace("spk_", "S")


@dataclass
class AWSTranscriptItem(AWSTimestamped):
    type: str = ""
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    segment: Optional[AWSSegment] = None

    @property
    def speaker(self):
        return self.segment.speaker_label

    @property
    def content(self) -> str:
        return self.alternatives[0]["content"]


class TranscriptItem:
    def to_string(self):
        return str(self)

    def to_rich_text(self):
        raise NotImplementedError

    def accepts(self, other: AWSTranscriptItem) -> bool:
        return False


@dataclass
class TextItem(TranscriptItem):
    text: str = ""
    speaker: str = "S0"
    segment_index: int = 0

    def to_rich_text(self):
        return RichText.plain_text(self.text)

    def accepts(self, other: AWSTranscriptItem) -> bool:
        if not isinstance(other, AWSTranscriptItem):
            return False

        if other.speaker != self.speaker:
            return False
        elif other.segment.index != self.segment_index:
            return False

        return True

    def __str__(self) -> str:
        return self.text

    def __add__(self, other):
        return TextItem(self.text + " " + str(other))

    def __iadd__(self, other):
        if isinstance(other, AWSTranscriptItem):
            if other.type != "punctuation":
                self.text += " "

            other = other.content
        else:
            self.text += " "

        self.text += str(other)
        return self


@dataclass
class Timestamp(TranscriptItem):
    delta: datetime.timedelta = None

    def to_rich_text(self):
        return RichText.code(str(self))

    @classmethod
    def from_start_time(cls, start_time):
        start_time = int(math.floor(float(start_time)))
        return cls(delta=datetime.timedelta(seconds=start_time))

    def __str__(self) -> str:
        """Provide str() for string output of transcripts."""
        return f"[{str(self.delta)}]"


@dataclass
class Transcript:
    """Structured representation of an audio transcript."""

    timestamp_every: int = 60
    next_timestamp: int = field(init=False)

    items: List[TranscriptItem] = field(default_factory=list)
    segments: List[AWSSegment] = field(default_factory=list)
    segment_index: int = 0
    n_speakers: int = 0

    @classmethod
    def from_aws_transcribe_json(cls, aws_json):
        """Create a transcript from the JSON results of an AWS Transcribe batch job."""
        if "jobName" in aws_json:
            aws_json = aws_json["results"]

        t = cls()

        t.n_speakers = aws_json["speaker_labels"]["speakers"]
        t.segments = [
            AWSSegment(index=i, **s)
            for i, s in enumerate(aws_json["speaker_labels"]["segments"])
        ]
        t.segment_index = 0

        for item in aws_json["items"]:
            t += item

        return t

    def items_by_speaker(self) -> List[List[TranscriptItem]]:
        """Group tokens in the transcript according to speaker segments."""
        by_speaker = []
        current = []

        current_speaker = None
        for item in self.items:
            will_append = True
            if isinstance(item, TextItem):
                if current_speaker is None:
                    current_speaker = item.speaker
                if current_speaker != item.speaker:
                    current_speaker = item.speaker
                    will_append = False

            if not will_append:
                by_speaker.append(current)
                current = []

            current.append(item)

        by_speaker.append(current)
        return by_speaker

    def to_string(self) -> str:
        """Convert the transcript into a string for simple output."""
        results = []

        for group in self.items_by_speaker():
            speaker = [g for g in group if isinstance(g, TextItem)][0].speaker
            item = f"{speaker}: {''.join([str(g) for g in group])}"
            results.append(item)

        return "\n".join(results)

    def to_block(self, block_title):
        """Convert the transcript into a Notion block object."""
        children = []
        for group in self.items_by_speaker():
            speaker = [g for g in group if isinstance(g, TextItem)][0].speaker
            text_items = [RichText.bold(speaker), RichText.plain_text(": ")]
            for g in group:
                text_items.append(g.to_rich_text())
                text_items.append(RichText.plain_text(" "))
            children.append(Block.paragraph(text_items))

        return Block.paragraph(block_title, children=children)

    def __post_init__(self):
        """Initialize the next timestamp we will add according to desired frequency."""
        self.next_timestamp = self.timestamp_every

    @property
    def current_segment(self):
        """Fetch the segment which we are consuming tokens for."""
        return self.segments[self.segment_index]

    def __iadd__(self, token):
        """Add a token (from the token utterance stream) to the transcript."""
        assert isinstance(token, dict)
        token = AWSTranscriptItem(**token)

        if token.type != "punctuation":
            while self.current_segment.end_time < token.start_time:
                self.segment_index += 1

        token.segment = self.current_segment

        if token.start_time and token.start_time > self.next_timestamp:
            self.items.append(Timestamp.from_start_time(token.start_time))
            self.next_timestamp += self.timestamp_every

        if self.items and self.items[-1].accepts(token):
            self.items[-1] += token
        else:
            self.items.append(
                TextItem(
                    token.content,
                    speaker=token.speaker,
                    segment_index=token.segment.index,
                )
            )

        return self
