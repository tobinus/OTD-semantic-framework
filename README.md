# OTD-semantic-framework
Ontology Based Semantic Framework for Open Transport Data 

This repository contains source-code and stubs of code used in the development
of the prototype OTD-semantic-framework. Its purpose is to help developers find
the datasets they want to use, by not requiring them to use the exact same words
in their search queries as those used by the dataset publishers.


## Preparing

This guide assumes you use Pipenv, but you may also use virtualenv/pip directly
using the requirements.txt files (though support for this may be dropped at a
future point).

1. Install Pipenv
2. While in this directory, run `pipenv install`
4. Follow the link in `ordvev/README.md` and extract the files into the `ordvev/` directory
5. Configure (and install if you haven't) MongoDB so you have a user (with password) which can access it
6. Create a file called `.env` in this directory, where you define the variables:
   * `DB_USERNAME`: Username to use when logging in to MongoDB
   * `DB_PASSWD`: Password to use when logging in to MongoDB
   * `DB_HOST`: Name of server where MongoDB runs. Defaults to localhost
   * `DB_NAME`: Name of database to use in MongoDB

   These can also be set as environment variables.


## Usage

Before the search engine can get up and running, there are a couple processes
that must be run. Specifically:

1. Pre-process ontology
   1. Upload ontology
   2. Compute similarities between concepts in ontology
2. Pre-process datasets
   1. Import (new) datasets
   2. Perform manual linking to concepts
   3. Perform automatic linking to concepts
   4. Compute similarities between datasets and concepts
3. Run search

Below, you'll find instructions for running these processes.
They all use the script `dataontosearch.py` to do different parts of the work;
you can explore the options by passing `--help` as an argument.


### Pre-processing of ontology

#### Upload ontology

1. Run `pipenv run python dataontosearch.py ontology create`
2. Note down the UUID you receive back
3. Add the following line in your `.env` file, replacing `<UUID>` with the UUID you got:
   
   ```
   ONTOLOGY_UUID=<UUID>
   ```

There are other commands you can use to manipulate and display ontologies, run `pipenv run python dataontosearch.py ontology --help` for a full list.

#### Link concepts to terms

TODO


#### Compute similarities between concepts in ontology

TODO


### Pre-processing of datasets

#### Import (new) datasets

TODO


#### Perform manual linking to concepts

1. Run `pipenv run python dataontosearch.py dataset_tagger`
2. Visit http://localhost:8000/about in your web browser
3. Follow the instructions for tagging datasets, using the UID you wrote down
   when you uploaded an ontology


#### Perform automatic linking to concepts

TODO


#### Compute similarities between datasets and concepts

TODO


### Run search

1. Configure so the right dataset-to-ontology tags are used (TODO)
2. Run `pipenv run python dataontosearch.py serve`
3. The webserver will perform some indexing. It will give you a signal when it's done
4. You may now search by visiting http://localhost:8000
