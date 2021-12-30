# Code for Voice Note transcription and syncing to Notion

The first order of business is using the Amazon Transcription API and S3.

# Installation

Create a user for the transcription service and put the credentials in the standard place (.aws/credentials) under
the username `voice_transcription_user`.

Create a bucket on S3 named `voice-transcription-notes`.
