from odinapi.views import baseview

import pytest


def test_inspect_predicate():
    class T:
        def test(self):
            pass

    assert baseview.inspect_predicate(T.test)


def test_inspect_predicate_on_instance():
    class T:
        def test(self):
            pass

    assert baseview.inspect_predicate(T().test)


def test_register_versions():
    class T:
        @baseview.register_versions('unlucky', ['v42'])
        def t(self):
            pass

    assert T.t._role == 'unlucky'
    assert T.t._versions == ['v42']


@pytest.mark.parametrize("role,versions,check_attribute,expect", (
    ('fetch', ['v42'], 'VERSION_TO_FETCHDATA', {'v42': '_tester'}),
    (
        'return', None, 'VERSION_TO_RETURNDATA',
        {'v4': '_tester', 'v5': '_tester'},
    ),
    ('swagger', ['v42'], 'VERSION_TO_SWAGGERSPEC', {'v42': '_tester'}),
))
def test_baseview(role, versions, check_attribute, expect):
    class Ultimate(baseview.BaseView):
        @baseview.register_versions(role, versions)
        def _tester(self):
            pass

    ult = Ultimate()
    assert getattr(ult, check_attribute) == expect
