from datetime import datetime
from unittest import TestCase

from odinapi.utils import time_util


class TestTimeConversions(TestCase):

    def test_stw(self):
        """Test conversion stw <-> datetime"""
        self.assertEqual(
            time_util.stw2datetime(7123991206),
            datetime(2015, 4, 1, 0, 3, 30, 290131))

        self.assertEqual(
            time_util.datetime2stw(datetime(2015, 4, 1, 0, 3, 30, 290131)),
            7123991206)
