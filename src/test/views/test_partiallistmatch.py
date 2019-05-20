import pytest

from .partiallistmatch import PartialListMatch


def test_list_partial_match_fails_bad_length():
    with pytest.raises(AssertionError, match='len missmatch'):
        assert [1, 2] == PartialListMatch(4, [1, 2], name='test')


def test_list_partial_match_fails_bad_part():
    with pytest.raises(AssertionError, match='partial equality fails'):
        assert [1, 2, 3] == PartialListMatch(3, [2, 3], name='test')


def test_list_partial_match_fails_bad_startidx():
    with pytest.raises(AssertionError, match='partial equality fails'):
        assert [1, 2, 3] == PartialListMatch(3, [1, 2], startidx=1)


@pytest.mark.parametrize('part,start', (
    ([1], 0),
    ([1, 2], 0),
    ([2, 3], 1),
))
def test_list_partial_match(part, start):
    assert [1, 2, 3, 4] == PartialListMatch(4, part, startidx=start)
