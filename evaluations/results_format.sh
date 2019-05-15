for FILE in results_*.csv
do
echo $FILE
python latex-table.py $FILE | xclip -sel clipboard
# Wait for enter
read HEI
done
