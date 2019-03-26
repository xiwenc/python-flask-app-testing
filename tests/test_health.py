from unittest import mock
from flask_testing import LiveServerTestCase

from app.main import App


# Example using Magick Mock
class TestHealth_sick(LiveServerTestCase):
    def setUp(self):
        self.client = self.app.test_client()
        super().setUp()

    def _arrange(self):
        self.expected_health = {"state": "sick"}
        mocked_mail_service = mock.Mock(autospec=True)
        mocked_mail_service.check = mock.MagicMock(
            return_value=self.expected_health,
        )
        return App(
            mail_service=mocked_mail_service,
        ).create_app()

    def _act(self):
        self.response = self.client.get("/health")

    def _assert(self):
        assert self.response.status_code == 200
        assert self.response.get_json() == self.expected_health

    def create_app(self):
        return self._arrange()

    def test_case(self):
        self._act()
        self._assert()
