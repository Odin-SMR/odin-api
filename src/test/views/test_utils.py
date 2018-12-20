# pylint: disable=no-self-use,redefined-outer-name,old-style-class,no-init

import pytest


from odinapi.views.utils import (
    make_rfc5988_link,
    OffsetAndLimitPagination,
)


def test_make_rfc5988_link():
    link = make_rfc5988_link(
        "https://foo.bar/", rel="alternate", title="Foobar")
    assert link == '<https://foo.bar/>; rel="alternate"; title="Foobar"'


class TestOffsetAndLimitPagination(object):

    @pytest.fixture
    def pagination(self):
        return OffsetAndLimitPagination(20, 10, 42)

    def test_get_next_page(self, pagination):
        assert pagination.get_next_page() == (30, 10)

    def test_get_prev_page(self, pagination):
        assert pagination.get_prev_page() == (10, 10)

    def test_get_previous_page(self, pagination):
        assert pagination.get_previous_page() == (10, 10)

    def test_get_first_page(self, pagination):
        assert pagination.get_first_page() == (0, 10)

    def test_get_last_page(self, pagination):
        assert pagination.get_last_page() == (40, 10)

    def test_get_self_page(self, pagination):
        assert pagination.get_self_page() == (20, 10)

    def test_get_prev_page_first(self):
        pagination = OffsetAndLimitPagination(0, 10, 42)
        assert pagination.get_prev_page() is None

    def test_get_prev_page_no_negative(self):
        pagination = OffsetAndLimitPagination(5, 10, 42)
        assert pagination.get_prev_page() == (0, 10)

    def test_get_next_page_last(self):
        pagination = OffsetAndLimitPagination(40, 10, 42)
        assert pagination.get_next_page() is None
