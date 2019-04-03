from unittest import mock
from flask_testing import LiveServerTestCase
from http import HTTPStatus

from app.main import App
from tests.base import AAAMixin


class TestHealth_sick(AAAMixin, LiveServerTestCase):
    """ Detect when mail service is in sick state """

    def ARRANGE(self):
        self.expected_health = {"mail_service": "sick"}
        mocked_mail_service = mock.Mock(autospec=True)
        mocked_mail_service.check = mock.MagicMock(
            return_value=self.expected_health["mail_service"],
        )
        return App(
            mail_service=mocked_mail_service,
        ).create_app()

    def ACT(self):
        return self.client.get("/health")

    def ASSERT(self):
        assert self.response.status_code == HTTPStatus.OK
        assert self.response.get_json() == self.expected_health


class TestHealth_integration(AAAMixin, LiveServerTestCase):
    """ Test against real mail service integration """

    def ARRANGE(self):
        self.expected_health = {"mail_service": "OK"}
        return App().create_app()

    def ACT(self):
        return self.client.get("/health")

    def ASSERT(self):
        assert self.response.status_code == HTTPStatus.OK
        assert self.response.get_json() == self.expected_health