# libgen-api-modern

Search Library Genesis programmatically using an enhanced Python library. This fork extends the original `libgen-api` by [Harrison Broadbent](https://github.com/harrison-broadbent/libgen-api) and `libgen-api-enhanced` by [Onurhan](https://github.com/onurhanak/libgen-api-enhanced) with added features like direct download links and book cover links. It also returns 100 results by default.

## Contents

- [libgen-api-modern](#libgen-api-modern)
  - [Contents](#contents)
  - [Getting Started](#getting-started)
  - [NOTICE](#notice)
    - [Non-fiction/Sci-tech](#non-fictionsci-tech)
    - [Fiction](#fiction)
  - [Basic Searching](#basic-searching)
    - [Title](#title)
    - [Author](#author)
  - [Filtered Searching](#filtered-searching)
    - [Filtered Title Searching](#filtered-title-searching)
    - [Non-exact Filtered Searching](#non-exact-filtered-searching)
  - [Results Layout](#results-layout)
    - [Non-fiction/sci-tech result layout](#non-fictionsci-tech-result-layout)
    - [Fiction result layout](#fiction-result-layout)
  - [Contributors](#contributors)

## Getting Started

Install the package -

using pipx

```
pipx install libgen-api-modern
```

using poetry

```
poetry add libgen-api-modern
```

## NOTICE

With libgen-api-modern library, you can search for:

- non-fiction/sci-tech
- fiction
- scientific articles - will be available soon.

Perform a basic search -

### Non-fiction/Sci-tech

```python
# search()

from libgen_api_modern import LibgenSearch
results = LibgenSearch.search("The Alchemist")
print(results)
```

### Fiction

```python
# search_fiction()

from libgen_api_modern import LibgenSearch
results = LibgenSearch.search_fiction("How to kill men and get away with it")
print(results)
```

## Basic Searching

Search by title or author:

### Title

```python
# search title

from libgen_api_modern import LibgenSearch
results = LibgenSearch.search("Pride and Prejudice", search_type = "title")
print(results)
```

### Author

```python
# search author

from libgen_api_modern import LibgenSearch
results = LibgenSearch.search("Jane Austen", search_type = "author")
print(results)
```

> You can provide title, author, ISBN, publisher, year, language, or series as arguments to search_type

## Filtered Searching

- You can define a set of filters, and then use them to filter the search results that get returned.
- By default, filtering will remove results that match the filters exactly (case-sensitive) -
  - This can be adjusted by setting `exact_match=True` when calling one of the filter methods, which allows for case-insensitive and substring filtering.

### Filtered Title Searching

```python
# search_filtered()

from libgen_api_modern import LibgenSearch

title_filters = {"Year": "2007", "Extension": "epub"}
titles = LibgenSearch.search_filtered("Pride and Prejudice", title_filters, exact_match=True)
print(titles)
```

### Non-exact Filtered Searching

```python
# search filtered 
# exact_match = False

from libgen_api_modern import LibgenSearch

partial_filters = {"Year": "2000"}
titles = LibgenSearch.search_filtered("Agatha Christie", partial_filters, exact_match=False)
print(titles)

```

## Results Layout

### Non-fiction/sci-tech result layout

Results are returned as a list of dictionaries:

```json
[
  {
    'Title': 'The war of art', 
    'Author(s)': 'Mits Free', 
    'Series': 'example series', 
    'Periodical': '', 
    'Publisher': 'Libre publishers', 
    'City': 'New York, NY', 
    'Year': '2002', 
    'Edition': '1st ed', 
    'Language': 'English', 
    'Pages': '165[159]', 
    'ISBN': '123456789', 
    'ID': '1487009', 
    'Size': '430 Kb (440781)', 
    'Extension': 'pdf', 
    'Cover': 'https://covers.xyz.jpg', 
    'Direct_Download_Link': 'https://download.xyz/book.pdf'
  }
]

```

### Fiction result layout

```json

[
  {
    'Title': 'How to Get Away With It', 
    'Language': 'English', 
    'Year': '1873', 
    'Publisher': 'Pub', 
    'Format': 'EPUB', 
    'ID': '4263532', 
    'Authors': 'John Doe', 
    'Cover': 'https://cover.xyz.book.jpg', 
    'Direct_Download_Link': 'https://download.xyz.book.epub'
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
