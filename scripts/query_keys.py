from enum import Enum

class QueryKeys(Enum):
    KG_BOOK = ("book", "books_from_kg", "number_of_static_results", None)
    # ROWS_BOOK = ("book", "books_from_rows", None, None)
    WEB = ("web", "webs", "number_of_web_results", None)
    MICRODATA = ("microdata", "microdatas", "number_of_extracted_microdata", None)
    OFFER = ("offer", "offers", None, True)
    PRICE = ("price", "prices", None, True)
    AVAILABILITY = ("availability", "availabilities", None, True)
    # BOOK_NAME = ("bookName", "book_names", None, True)
    PUBLISHER_NAME = ("publisher", "publishers", None, True)

    def __init__(self, query_key, result_key, stats_key, is_feature):
        self.query_key = query_key
        self.result_key = result_key
        self.stats_key = stats_key
        self.is_feature = is_feature