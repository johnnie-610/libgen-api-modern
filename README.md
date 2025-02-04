# libgen-api-modern

Search Library Genesis programmatically using an enhanced Python library. This fork extends the original `libgen-api` by [Harrison Broadbent](https://github.com/harrison-broadbent/libgen-api) and `libgen-api-enhanced` by [Onurhan](https://github.com/onurhanak/libgen-api-enhanced) with added features like direct download links and book cover links. It also returns 100 results by default.

## Contents

- [libgen-api-modern](#libgen-api-modern)
  - [Contents](#contents)
  - [What's New](#whats-new)
  - [Getting Started](#getting-started)
  - [Filtered Searching](#filtered-searching)
    - [Filtered Title Searching](#filtered-title-searching)
    - [Non-exact Filtered Searching](#non-exact-filtered-searching)
  - [Results Layout](#results-layout)
    - [Non-fiction/sci-tech result layout](#non-fictionsci-tech-result-layout)
  - [Contributors](#contributors)

## What's New

- Added direct download links for books
- Added book cover links
- Added 100 results by default
- Added support for filtering
Please Note that this README may not show exact results as from using the library. THIS IS A WORK IN PROGRESS, IT'LL BE UPDATED AS THE LIBRARY DEVELOPMENT GOES ON.

## Getting Started

Install the package -

```shell

pip install libgen-api-modern

```

Perform a basic search -

```python

await LibgenSearch.search("Pride and Prejudice")

```

## Filtered Searching

- You can define a set of filters, and then use them to filter the search results that get returned.
- By default, filtering will remove results that match the filters exactly (case-sensitive) -
  - This can be adjusted by setting `exact_match=True` when calling one of the filter methods, which allows for case-insensitive and substring filtering.

### Filtered Title Searching

```python
# search_filtered()

title_filters = {"Year": "2007", "Extension": "epub"}
titles = await LibgenSearch.search_filtered("Pride and Prejudice", title_filters, exact_match=True)
print(titles)
```

### Non-exact Filtered Searching

```python
# search filtered
# exact_match = False

partial_filters = {"Year": "2000"}
titles = await LibgenSearch.search_filtered("Agatha Christie", partial_filters, exact_match=False)
print(titles)

```

## Results Layout

### Non-fiction/sci-tech result layout

Results are returned as a python object.

```python

BookData:
    id: str
    authors: tuple[str, ...]
    title: str
    publisher: str | None
    year: str | None
    pages: str | None
    language: str | None
    size: str | None
    extension: str | None
    isbn: str | None
    cover_url: str | None
    download_links: DownloadLinks | None

```
ALSO NOTE: `download_links` is a `DownloadLinks` object.

```python

DownloadLinks:
    get_link: str | None
    cloudflare_link: str | None
    ipfs_link: str | None
    pinata_link: str | None
    cover_link: str | None

```

## Contributors

Please don't hesitate to raise an issue, or [fork this project](https://github.com/johnnie-610/libgen-api-modern) and improve on it.

Thanks to the following people:

- [harrison-broadbent](https://github.com/harrison-broadbent) who wrote the original Libgen API.
- [calmoo](https://github.com/calmoo)
- [HENRYMARTIN5](https://github.com/HENRYMARTIN5)
- [Onurhan](https://github.com/onurhanak)

Please star [this library on Github](https://github.com/johnnie-610/libgen-api-modern) if you like it.
