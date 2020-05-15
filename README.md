# preprints-refs-collector
preprints-refs-collector will collect the metadata of manuscripts submitted to biorRxiv/medRxiv/arXiv, check for some keywords of interests in the title/abstract, download and parse the PDFs of those submissions, and parse them using the Crossref REST API.

There are two ways to extract the references from the PDFs:
The first uses Cermine, which will parse the citations, but it will miss a lot of citations.
cermine standalone: https://maven.ceon.pl/artifactory/kdd-releases/pl/edu/icm/cermine/cermine-impl/1.13/

The other is refextract, which will extract free-form references. Because we use the CrossRef search engine to match the citations, this approach is preferred.

Additional Requierements:
JDK
Chrome driver for Selenium (has to match the version installed on your computer): https://chromedriver.chromium.org/downloads

You will need to create add the Chrome driver in the tools folder, and the Cermine jar if you chose to use this option.

## Get started
You can run every module individually, or they can be called specifically. The first time you run the script you need to specify a starting date, and the script will collect the data from that time up until now.

For instance: 

```
python main.py all 2020-01-01 
```

Will run all modules on documents submitted after this date.

The code can be called without a date subsequently and only the new submissions will be added.