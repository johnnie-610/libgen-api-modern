# libgen-api-modern

Search Library Genesis programmatically using an enhanced Python library. This fork extends the original `libgen-api` by [Harrison Broadbent](https://github.com/harrison-broadbent/libgen-api) and `libgen-api-enhanced` by [Onurhan](https://github.com/onurhanak/libgen-api-enhanced) with added features like direct download links and book cover links. It also returns 100 results by default.

## Contents

- [libgen-api-modern](#libgen-api-modern)
  - [Contents](#contents)
  - [Getting Started](#getting-started)
  - [Basic Searching:](#basic-searching)
    - [Title:](#title)
    - [Author:](#author)
  - [Filtered Searching](#filtered-searching)
    - [Filtered Title Searching](#filtered-title-searching)
    - [Filtered Author Searching](#filtered-author-searching)
    - [Non-exact Filtered Searching](#non-exact-filtered-searching)
  - [Results Layout](#results-layout)
  - [Contributors](#contributors)

## Getting Started

Install the package -

```
pip install libgen-api-modern
```

Perform a basic search -

```python
# search_title()

from libgen_api_modern.libgen_search import LibgenSearch
s = LibgenSearch()
results = s.search_title("Pride and Prejudice")
print(results)
```

Check out the [results layout](#results-layout) to see available fields and how the results data is formatted.

## Basic Searching:

Search by title or author:

### Title:

```python
# search_title()

from libgen_api_modern.libgen_search import LibgenSearch
s = LibgenSearch()
results = s.search_title("Pride and Prejudice")
print(results)
```

### Author:

```python
# search_author()

from libgen_api_modern.libgen_search import LibgenSearch
s = LibgenSearch()
results = s.search_author("Jane Austen")
print(results)
```

## Filtered Searching

- You can define a set of filters, and then use them to filter the search results that get returned.
- By default, filtering will remove results that do not match the filters exactly (case-sensitive) -
  - This can be adjusted by setting `exact_match=False` when calling one of the filter methods, which allows for case-insensitive and substring filtering.

### Filtered Title Searching

```python
# search_title_filtered()

from libgen_api_modern.libgen_search import LibgenSearch

tf = LibgenSearch()
title_filters = {"Year": "2007", "Extension": "epub"}
titles = tf.search_title_filtered("Pride and Prejudice", title_filters, exact_match=True)
print(titles)
```

### Filtered Author Searching

```python
# search_author_filtered()

from libgen_api_modern.libgen_search import LibgenSearch

af = LibgenSearch()
author_filters = {"Language": "German", "Year": "2009"}
titles = af.search_author_filtered("Agatha Christie", author_filters, exact_match=True)
print(titles)
```

### Non-exact Filtered Searching

```python
# search_author_filtered(exact_match = False)

from libgen_api_modern.libgen_search import LibgenSearch

ne_af = LibgenSearch()
partial_filters = {"Year": "200"}
titles = ne_af.search_author_filtered("Agatha Christie", partial_filters, exact_match=False)
print(titles)

```

## Results Layout

Results are returned as a list of dictionaries:

```json
[
    {
        "Title": "Example title",
        "Author(s)": "Example author(s)",
        "Series": "Example series",
        "Periodical": "Example periodical",
        "Publisher": "Example publisher",
        "City": "Example city",
        "Year": "Example year",
        "Edition": "Example edition",
        "Language": "Example language",
        "Pages": "Example pages",
        "ISBN": "Example ISBN",
        "ID": "Example id",
        "Size": "Example size",
        "Extension": "Example extension",
        "Cover": "Example cover link",
        "MD5": "Example hash",
        "Direct_Download_Link": "Example link"
    }
]

```

## Contributors

Please don't hesitate to raise an issue, or fork this project and improve on it.

Thanks to the following people:

- [harrison-broadbent](https://github.com/harrison-broadbent) who wrote the original Libgen API.
- [calmoo](https://github.com/calmoo)
- [HENRYMARTIN5](https://github.com/HENRYMARTIN5)
- [Onurhan](https://github.com/onurhanak)
