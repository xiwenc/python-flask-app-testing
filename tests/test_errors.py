from unittest import mock
from flask_testing import LiveServerTestCase
from http import HTTPStatus

from app.main import App
from tests.base import AAAMixin


class TestErrors_not_found(AAAMixin, LiveServerTestCase):
    """ Unknown path result in Not Found """

    def ARRANGE(self):
        return App().create_app()

    def ACT(self):
        return self.client.get("/i-do-not-exist")

    def ASSERT(self):
        assert self.response.status_code == HTTPStatus.NOT_FOUND


class TestErrors_throw_exception(AAAMixin, LiveServerTestCase):
    """ Exceptions result in internal server error """

    def ARRANGE(self):
        return App().create_app()

    def ACT(self):
        return self.client.put("/throw-exception")

    def ASSERT(self):
        assert self.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
