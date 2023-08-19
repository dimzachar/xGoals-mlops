#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/../../config.env"
CONFIG_PATH="$DIR/../../config.json"

python src/pipeline/orchestrate.py --config "$CONFIG_PATH"
