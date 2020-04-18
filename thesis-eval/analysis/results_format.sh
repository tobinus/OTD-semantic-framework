#!/bin/bash
# Make it easy to copy Latex over to Latex documents, using CSV files from the results ODS file
set -o errexit
set -o nounset
set -o pipefail

for FILE in "$@"
do
echo $FILE
python latex-table.py $FILE | xclip -sel clipboard
# Wait for enter
read HEI
done
