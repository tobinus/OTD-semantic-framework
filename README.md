# OTD-semantic-framework
Ontology Based Semantic Search for Open Transport Data 

This repository contains source-code and stubs of code used in the development
of the prototype **DataOntoSearch**. Its purpose is to help developers find
the datasets they want to use, by not requiring them to use the exact same words
in their search queries as those used by the dataset publishers.


## Preparing

This guide assumes you use Pipenv, but you may also use virtualenv/pip directly
using the requirements.txt files (though support for this may be dropped at a
future point).

**Reading this guide**: Any Python commands in the instructions assume you
already have the virtual environment loaded. With _Pipenv_, you do this by
running `pipenv shell`, or you can prepend `pipenv run` to whatever you want to
run inside the virtual environment. With Pip and Virtualenv, you do this by
sourcing the `activate` inside the virtual environment folder. For example, if
the virtual environment folder is called `venv`, you run `. venv/bin/activate`.

1. (Fork and) clone this repository, so you have a copy locally
1. Install Pipenv (if so desired)
2. While in this directory, run `pipenv install`. Pip+Virtualenv users should
   set up the virtual environment and install from `requirements.txt` now
4. Follow the link in `ordvev/README.md` and extract the files into the `ordvev/` directory
5. Configure (and install if you haven't) MongoDB so you have a user (with password) which can access it. You will also need to enable authentication. See for example the [official guide from MongoDB](https://docs.mongodb.com/manual/tutorial/enable-authentication/).
6. Create a file called `.env` in this directory, where you define the variables:
   * `DB_USERNAME`: Username to use when logging in to MongoDB
   * `DB_PASSWD`: Password to use when logging in to MongoDB
   * `DB_HOST`: Name of server where MongoDB runs. Defaults to localhost
   * `DB_NAME`: Name of database to use in MongoDB. Defaults to ontodb
   
   To define for example `DB_USERNAME` to be `john`, you would write:
   
   ```bash
   DB_USERNAME=john
   ```
   
   These can also be set as [environment variables](https://en.wikipedia.org/wiki/Environment_variable).
7. Download the different data for [nltk](https://www.nltk.org/data.html), used for word tokenizing, removing stop words and the like. You can do this by running `python dataontosearch.py nltk_data`.



## Usage

Before the search engine can get up and running, there are a couple processes
that must be run. Specifically:

1. Pre-process ontology
   1. Upload ontology
2. Pre-process datasets
   1. Import (new) datasets
   2. Perform manual linking to concepts
   3. Perform automatic linking to concepts
3. Run search

Below, you'll find instructions for running these processes.
They all use the script `dataontosearch.py` to do different parts of the work;
you can explore the options by passing `--help` as an argument.


### Entities

There are four types of graphs in the application:

1. **Ontology**: Concepts and their relation to one another
2. **Dataset**: Available datasets in DCAT format
3. **Similarity**: Similarity graph, linking datasets to concepts manually
4. **Autotag**: Similarity graph, linking datasets to concepts automatically

These entities are managed through their own subcommands, in a fairly consistent
way. They all have a canonical version, which is used by default. It is also
possible to load a custom graph into the database.

In addition, there are different kinds of matrices used:

1. **Concept-concept similarity matrix**: Similarities between concepts,
   calculated using Wu-Palmer similarity.
2. **Concept-dataset similarity matrix for manual tagging**: Similarities
   between datasets and concepts, enriched by the concept-concept similarity
   matrix.
3. **Concept-dataset similarity matrix for automatic tagging**: Same as above,
   except this uses the _autotag_ graph rather than the _similarity_ one.
   
Since they are all derivatives of graphs, they are automatically created when
needed, and re-created whenever the graph they directly depend on (ontology, 
similarity and autotag respectively) changes or is updated.


### Choosing graphs to use

For each of the graphs mentioned above, the application's choice of graph to
use is done like this:

1. Has a UUID been specified using CLI options or the like (where available)?
   If so, use the specified graph.
2. Has a UUID been specified using the environment variable named 
   `<GRAPH-NAME>_UUID`, where `<GRAPH-NAME>` is the upper-cased name of the
   graph? If so, use the specified graph.
3. If no graph has been specified this far, then whatever graph is returned
   first by MongoDB is used. (Though note there are exceptions where an error is
   raised instead, the goal is to eliminate those exceptions.)
   
Suggested approaches:
* Keep only one version of each graph type, so it is obvious which one
  is picked by MongoDB.
  * You don't need to specify what graph to use this way.
  * However, if there are more than one graph, you may encounter subtle bugs
    due to an unexpected graph being used.
* Specify the UUID of the graph to use in the `.env` file, using the appropriate
  environment variables.
  * Works well when you'd like to switch between different graphs.
  * You may override the `.env` variables on the command line.
  * Though this means you must manage the UUIDs of graphs.


### Pre-processing of ontology

#### Upload ontology

1. Run `python dataontosearch.py ontology create`

There are other commands you can use to manipulate and display ontologies, run `python dataontosearch.py ontology --help` for a full list.

### Pre-processing of datasets

#### Import (new) datasets

1. Run `python dataontosearch.py dataset create --ckan <CKAN-URL>`
   where you replace `<CKAN-URL>` with the base URL to your CKAN instance. The
   instance must also expose RDF information about each dataset.

You may also create your own graph, and load it into the database. Use the
`--help` option to see your options.


#### Perform manual linking to concepts

You may use the existing tags. Simply run:

`python dataontosearch.py similarity create`

Alternatively, you can do custom tagging, though this has not been tested at
this point.

1. Run `python dataontosearch.py dataset_tagger`
2. Visit http://localhost:8000/about in your web browser
3. Follow the instructions for tagging datasets, using the UID you wrote down
   when you uploaded an ontology


#### Perform automatic linking to concepts

Run the following:

`python dataontosearch.py autotag create`

Again, append `--help` to see available options.

**WARNING 1**: The autotag script requires around 2 GB of RAM(!) for the Python process, meaning
that it may get killed on systems with not enough memory. You may choose to run
the autotag process on a different system, instead of on the server intended for serving the search.

**WARNING 2**: This script can take a long time to run, like 45 minutes or even an hour.
It is not able to continue where it left out, so you might want to run this in
`tmux`, `screen` or something similar when running on a server over SSH (so the
process survives a disconnect).


### Run search

1. Run `python dataontosearch.py serve`
2. The webserver will perform some indexing, creating necessary matrices. It will give you a signal when it's done
3. You may now search by visiting http://localhost:8000

Alternatively, you may search using the command line interface directly.
Run `python dataontosearch.py search --help` for more information.
