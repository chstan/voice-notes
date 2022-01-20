#!/bin/sh
STARTDIR=`$(pwd)`
TOML_DIR=/home/moose/conrad/GitHub/voice-notes
cd "$TOML_DIR" || exit
poetry run bash -c "python scripts/create_month_and_day_planning_page.py --day_delta=1 $* && cd $STARTDIR"
poetry run bash -c "python scripts/create_month_and_day_planning_page.py --day_delta=2 $* && cd $STARTDIR"
