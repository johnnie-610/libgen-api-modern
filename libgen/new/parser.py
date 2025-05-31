# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
#  libgen/new/parser.py
#
# This file is part of the libgen-api-modern library


from html.parser import HTMLParser


class LibgenHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset_parser()

    def reset_parser(self):
        self.in_table = False
        self.in_td = False
        self.current_row = []
        self.results = []
        self.data_buffer = ""
        self.td_count = 0
        self.current_cover = ""  # cover image link from first cell
        self.current_mirror = ""  # mirror link from the last cell

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and attrs.get("id") == "tablelibgen":
            self.in_table = True
        if self.in_table and tag == "tr":
            self.current_row = []
            self.td_count = 0
            self.current_cover = ""
            self.current_mirror = ""
        if self.in_table and tag == "td":
            self.in_td = True
            self.data_buffer = ""
            self.td_count += 1
        # For the first cell (cover), capture the image src
        if self.in_td and self.td_count == 1 and tag == "img":
            self.current_cover = attrs.get("src", "")
        # For the mirror cell (assumed to be the 10th column), capture the first link's href.
        if self.in_td and self.td_count == 10 and tag == "a":
            if not self.current_mirror:
                self.current_mirror = attrs.get("href", "")

    def handle_data(self, data):
        if self.in_td:
            self.data_buffer += data.strip() + " "

    def handle_endtag(self, tag):
        if self.in_table and tag == "td":
            self.in_td = False
            if self.td_count == 1:
                self.current_row.append(self.current_cover)
            elif self.td_count == 10:
                self.current_row.append(self.current_mirror)
            else:
                self.current_row.append(self.data_buffer.strip())
        if self.in_table and tag == "tr":
            if len(self.current_row) >= 10:
                result = {
                    "cover": self.current_row[0],
                    "title": self.current_row[1],
                    "authors": self.current_row[2],
                    "publisher": self.current_row[3],
                    "year": self.current_row[4],
                    "language": self.current_row[5],
                    "pages": self.current_row[6],
                    "size": self.current_row[7],
                    "extension": self.current_row[8],
                    "mirror": self.current_row[9],
                }
                self.results.append(result)
        if tag == "table" and self.in_table:
            self.in_table = False

    def get_results(self) -> list:
        return self.results
