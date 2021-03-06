# API Documentation

The endpoint available through the DataOntoSearch is documented below.

The documentation format is similar to that of `dataset_tagger`.


## Overview

| Method | Endpoint | Purpose |
| ------ | -------- | ------- |
| `GET`  | `/api/v1/search` | Perform a search |


## `GET /api/v1/search`

Perform a semantic search using DataOntoSearch.

### Query parameters

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| **`q`** | string | Query to perform |
| **`c`** | string | Optional. The Configuration to use. When not provided, the default configuration is used (the same as for the web interface) |
| **`a`** | number | Optional. Set to 1 in order to use the automatically tagged data, instead of the manual tags (the default) |
| **`d`** | number | Optional. Set to 0 to avoid retrieving metadata about the matched datasets. The title and description fields will be `null` in that case |
| **`ic`** | number | Optional. Set to 0 to avoid retrieving concepts related to the query and datasets |
| **`qcs`** | float | Optional. The query-concept similarity threshold, default: 0.0 |
| **`qds`** | float | Optional. The query-dataset similarity threshold, default: 0.75 |


### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | |
| **`concepts`** | array | The concepts regarded as the most similar to the query, sorted with the most relevant first |
| **`concepts[]`** | object | One matching concept |
| **`concepts[].uri`** | string | The RDF IRI of this concept |
| **`concepts[].label`** | string | The preferred label for this concept |
| **`concepts[].similarity`** | number | The similarity score between the query and this concept |
| **`results`** | array | The datasets regarded as the most similar to the query, sorted with the most relevant first |
| **`results[]`** | object | One matching dataset |
| **`results[].score`** | number | The similarity score between the query and this dataset |
| **`results[].title`** | string | This dataset's title |
| **`results[].description`** | string | This dataset's description |
| **`results[].uri`** | string | This dataset's RDF IRI |
| **`results[].concepts`** | array | The concepts regarded as the most similar to this dataset (independently of the query) |
| **`results[].concepts[]`** | object | One related concept |
| **`results[].concepts[].uri`** | string | The RDF IRI of this concept |
| **`results[].concepts[].label`** | string | The preferred label for this concept |
| **`results[].concepts[].similarity`** | number | The similarity score between this dataset and this concept |

