from collections import namedtuple

## dcat:Dataset
Dataset = namedtuple('Dataset', 'title description issued modified identifier keyword language contactPoint temporal spatial accrualPeriodicity landingPage')
Dataset.__new__.__defaults__ = (None,) * len(Dataset._fields)


## dcat:Distribution
Distribution = namedtuple('Distribution', 'title description issued modified license_ rights accessURL downloadURL mediaType format_ bytesize')
Distribution.__new__.__defaults__ = (None,) * len(Distribution._fields)


## dcat:CatalogRecord
CatalogRecord = namedtuple('CatalogRecord', 'title description issued modified');
CatalogRecord.__new__.__defaults__ = (None,) * len(CatalogRecord._fields)


## dcat:Catalog
Catalog = namedtuple('Catalog', 'title description issued modified language license rights spatial homepage')
Catalog.__new__.__defaults__ = (None,) * len(Catalog._fields)
