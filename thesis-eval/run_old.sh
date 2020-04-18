#!/bin/bash
# Run queries with DataOntoSearch v1 while generating results that evaluate understands
. venv/bin/activate
set -o errexit
set -o nounset
set -o pipefail

FIRST_LOOP=1
# Note: This is only used for the reporting, you'll need to set graph env vars manually
# (Configuration was not a thing in the old DataOntoSearch)
CONFIGURATION="5c7ea259c556bb42803fa17e"
SIMTYPE="tagged"

# Loop through queries, given as arguments
for QUERY in "$@"
do
    if [ $FIRST_LOOP -eq 1 ]
    then
        FIRST_LOOP=0
    else
        # Ensure blank line between results
        echo
    fi
    echo "{\"configuration\": \"${CONFIGURATION}\", \"query\": \"${QUERY}\", \"engine\": \"old\"}"
    python dataontosearch.py search --simple $SIMTYPE "$QUERY"
done
