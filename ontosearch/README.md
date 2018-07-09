Register a new dataset

curl -i -H "Content-Type: application/json" -X POST -d '{"uri":"http://78.91.98.234:5000/dataset/nasjonale-rutedata-for-norge.rdf"}' http://localhost:5000/dataset/register

curl -i -H "Content-Type: application/json" -X POST -d '{"uri":"http://78.91.98.234:5000/dataset/satellittdata-no.rdf"}' http://localhost:5000/dataset/register

curl -H "Content-Type: application/json" -X POST http://localhost:5000/similarity/register -d @satellittdata.json

