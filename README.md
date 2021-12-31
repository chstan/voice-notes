# What is this?

This is a system I use to take notes on a voice recorder and have them transcribed for me into my Notion planner automatically.

This works by archiving mp3s on S3, transcribing them with AWS Transcribe, structuring the transcripts and attaching useful 
metadata including timestamps into the original media, and synchronizing the finished product into my agenda and notes page.

If you are interested, the code should be straightforward and self explanatory. You can look at the contents of `scripts/`
which serves as a collection of entrypoints into the project.

# External requirements and installation

You need an IAM account with S3 and AWS Transcribe privileges. You also need an Notion integration and associated keys.
You should place these in `~/.voice-notes/secrets/` in environment files according to the expectations of the configuration
class in `voice_notes/config.py`.

Briefly these environment variables required are:

`NOTION_TOKEN=`: The Notion integration API key.
`AWS_SLUG=`: A URL prefix which is required to generate media links in Notion. The Notion API unfortunately does not support file uploads yet.

AWS credentials are managed through `~/.aws` conventions, as is typical. It would be simple to refactor, if needed, to provide these credentials via the secrets .env file, so long as you modify `voice_notes/config.py:Config.__post_init__` to
load the profile from environment variables rather than through the profile name.

A few other pieces of configuration are hardcoded. Some, like the name of the bucket on S3 used for mp3 storage, can be
refactored. Others, like my conventions on the structure of my Notion agenda page require just a little bit more work.