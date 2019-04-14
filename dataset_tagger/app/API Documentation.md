# API Documentation

The endpoints available through the dataset_tagger are documented below.

**URL variables** describe parts of the URL which are variable, denoted by angle brackets. Currently, only the Configuration UUID is in use. It must be set so that the application knows what set of graphs to use (see the entity description in the root README).

**Query parameters** describe what GET query parameters are available to use.

Similarly, **JSON payload** describes the format of the JSON you must send as the POST payload. The names found on https://www.json.org are used to describe the types. Note that the `Content-Type` header must be set appropriately, for example `application/json`.

Finally, **Response JSON** describes the JSON returned by the dataset_tagger in response to your query.

**Note**: Usually, there are two ways of specifying a dataset.

* You can use the RDF IRI, which identifies the dataset in the RDF. This is called `dataset_id`, but should not be confused with the ID associated with the dataset in e.g. CKAN.
* Or you can use a URL at which the system can download RDF information about the dataset. This is called `dataset_url`, but should not be confused with the RDF IRI, URI or URL. The RDF IRI is extracted by finding the first dataset described in the downloaded graph.

"RDF URI" and "RDF IRI" are used interchangeably, though the latter is more correct (see the [RDF spec](https://www.w3.org/TR/rdf11-concepts/#resources-and-statements)).

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
| **dataset_id** or **dataset_url** | string | Optional. If not provided, taggings for all datasets are retrieved. Use `dataset_id` if you have the RDF IRI of the dataset to retrieve tagged concepts for, or use `dataset_url` if you have the URL from which DCAT RDF about the dataset can be downloaded

### Response JSON

**If `dataset_id` or `dataset_url` was provided:**

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | Represents the specified dataset |
| **title** | string | Title of the specified dataset |
| **concepts** | array of object | List of concepts associated with the specified dataset |
| **concepts[].uri** | string | RDF URI of this concept |
| **concepts[].label** | string | Human readable label for this concept |

**If neither `dataset_id` nor `dataset_url` were provided:**


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
| **dataset_url** | string | URL at which RDF DCAT information about the dataset can be found. Used to identify which dataset `concept` shall be associated with, and to download metadata if this dataset has not been seen before. Because of this last usage, it is not possible to specify the `dataset_id` directly |
| **concept** | string | Either RDF URI or the label of the concept to associate with `dataset_url` |

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
| **dataset_id** or **dataset_url** | string | The dataset to disassociate with `concept`. Use `dataset_id` if you have the RDF IRI of the dataset in question, or use `dataset_url` if you have the URL from which DCAT RDF about the dataset can be downloaded
| **concept** | string | Either RDF URI or the label of the concept to disassociate with `dataset_id`/`dataset_url` |

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
| **dataset_id** or **dataset_url** | string | The dataset to remove all traces of. Use `dataset_id` if you have the RDF IRI of the dataset in question, or use `dataset_url` if you have the URL from which DCAT RDF about the dataset can be downloaded

### Response JSON

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| _root_    | object | 
| **success** | bool | `true` if the dataset and its taggings were removed successfully, `false` if the dataset could not be found in the data store |
| **error** | string | Error message. Only present if `success` if `false` |

Note: On any error other than not finding the dataset, this endpoint currently raises an exception and fails with a 500 Internal error status message.
