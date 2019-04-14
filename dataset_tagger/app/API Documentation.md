# API Documentation

The endpoints available through the dataset_tagger are documented below.

**URL variables** describe parts of the URL which are variable, denoted by angle brackets. Currently, only the Configuration UUID is in use. It must be set so that the application knows what set of graphs to use (see the entity description in the root README).

**Query parameters** describe what GET query parameters are available to use.

Similarly, **JSON payload** describes the format of the JSON you must send as the POST payload. The names found on https://www.json.org are used to describe the types. Note that the `Content-Type` header must be set appropriately, for example `application/json`.

Finally, **Response JSON** describes the JSON returned by the dataset_tagger in response to your query.

## Overview

| Method | Endpoint | Purpose |
| ------ | -------- | ------- |
| `GET`  | `/api/v1/<uuid>/concept` | Retrieve concepts available to you |
| `GET`  | `/api/v1/<uuid>/tagging` | Retrieve existing taggings between dataset and concepts |
| `POST` | `/api/v1/<uuid>/tagging` | Create a new tagging between a dataset and a concept |
| `DELETE` | `/api/v1/<uuid>/tagging` | Remove a tagging between a dataset and a concept |
| `DELETE` | `/api/v1/<uuid>/dataset` | Remove a dataset and all associated taggings |


## `GET /api/v1/<uuid>/concept`

Retrieve the concepts in the ontology.

### URL Variables

| Variable | Description |
| -------- | ----------- |
| **uuid** | UUID of the Configuration to use |

### Query parameters

No parameters are accepted.

### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | Each member of this object represents a concept |
| **`<URI>`** | string | URI is the RDF URI of a concept in the ontology. The value is a human-readable label for this concept |


## `GET /api/v1/<uuid>/tagging`

Retrieve the existing taggings between datasets and concepts.

### URL Variables

| Variable | Description |
| -------- | ----------- |
| **uuid** | UUID of the Configuration to use |

### Query parameters

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| **dataset** | string | Optional. RDF URI of the dataset to retrieve tagged concepts for. If not provided, taggings for all datasets are retrieved |

### Response JSON

**If `dataset` was provided:**

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | Represents the specified dataset |
| **title** | string | Title of the specified dataset |
| **concepts** | array of object | List of concepts associated with the specified dataset |
| **concepts[].uri** | string | RDF URI of this concept |
| **concepts[].label** | string | Human readable label for this concept |

**If `dataset` was NOT provided:**


| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | Each member of this object represents a dataset |
| **`<URI>`** | object | URI is the RDF URI of a dataset for which a tagging exists |
| **`<URI>`.title** | string | Title of this dataset |
| **`<URI>`.concepts** | array of object | List of concepts associated with this dataset |
| **`<URI>`.concepts[].uri** | string | RDF URI of this concept |
| **`<URI>`.concepts[].label** | string | Human readable label for this concept |


## `POST /api/v1/<uuid>/tagging`

Create a new tagging between a dataset and a concept. If the dataset has not been encountered yet, it will be added to the data store.

### URL Variables

| Variable | Description |
| -------- | ----------- |
| **uuid** | UUID of the Configuration to use |

### JSON payload

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **dataset** | string | URL at which RDF DCAT information about the dataset can be found. Used to identify which dataset `concept` shall be associated with, and to download metadata if this dataset has not been seen before |
| **concept** | string | Either RDF URI or the label of the concept to associate with `dataset` |

### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **success** | bool | `true` if the tagging was added successfully, `false` if an error occurred |
| **id** | string | ID of the newly added tagging. Only present if `success` is `true` |
| **message** | string | Error message. Only present if `success` is `false` |


## `DELETE /api/v1/<uuid>/tagging`

Remove an existing tagging between a dataset and a concept.

### URL Variables

| Variable | Description |
| -------- | ----------- |
| **uuid** | UUID of the Configuration to use |

### JSON payload

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **dataset** | string | URL at which RDF DCAT information about the dataset can be found. The content at the URL is used to identify which dataset to disassociate with `concept` |
| **concept** | string | Either RDF URI or the label of the concept to disassociate with `dataset` |

### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **success** | bool | `true` if the tagging was removed successfully |

Note: On error, this endpoint currently raises an exception and fails with a 500 Internal error status message.


## `DELETE /api/v1/<uuid>/dataset`

Remove all taggings associated with the specified dataset, and remove it from the data store.

### URL Variables

| Variable | Description |
| -------- | ----------- |
| **uuid** | UUID of the Configuration to use |

### JSON payload

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **dataset** | string | URL at which RDF DCAT information about the dataset can be found. The content at the URL is used to identify which dataset to remove all traces of |

### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **success** | bool | `true` if the dataset and its taggings were removed successfully, `false` if the dataset could not be found in the data store |
| **error** | string | Error message. Only present if `success` if `false` |

Note: On any error other than not finding the dataset, this endpoint currently raises an exception and fails with a 500 Internal error status message.
