from collections import namedtuple

from flask import url_for


def copyemptydict(a):
    b = dict()
    for key in a:
        b[key] = []
    return b


def make_rfc5988_link(url, **params):
    link = "<{url}>".format(url=url)
    if params:
        params_str = "; ".join('{}="{}"'.format(k, params[k]) for k in params)
        link += "; " + params_str
    return link


def make_rfc5988_pagination_header(offset, limit, count, url_endpoint, **url_values):
    pagination = OffsetAndLimitPagination(offset, limit, count)
    pages = {
        "first": pagination.get_first_page(),
        "prev": pagination.get_prev_page(),
        "next": pagination.get_next_page(),
        "last": pagination.get_last_page(),
    }
    links = []
    for rel in pages:
        page = pages[rel]
        if page is not None:
            page_url_values = dict(url_values)
            page_url_values.update(page._asdict())
            url = url_for(url_endpoint, _external=True, **page_url_values)
            links.append(make_rfc5988_link(url, rel=rel))
    return ", ".join(links)


class OffsetAndLimitPagination:
    Page = namedtuple("Page", ["offset", "limit"])

    def __init__(self, offset, limit, count):
        self.offset = offset
        self.limit = limit
        self.count = count

    def get_first_page(self):
        return self.Page(0, self.limit)

    def get_prev_page(self):
        if self.offset > 0:
            return self.Page(max(0, self.offset - self.limit), self.limit)
        return None

    def get_previous_page(self):
        return self.get_prev_page()

    def get_self_page(self):
        return self.Page(self.offset, self.limit)

    def get_next_page(self):
        if self.offset + self.limit < self.count:
            return self.Page(self.offset + self.limit, self.limit)
        return None

    def get_last_page(self):
        return self.Page(self.count // self.limit * self.limit, self.limit)
