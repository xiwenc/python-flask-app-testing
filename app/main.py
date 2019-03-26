from flask import request, jsonify, make_response
from flask import Flask


class App(object):

    def __init__(self, mail_service=None):
        app = Flask(__name__)
        app.app_context().push()

        if not mail_service:
            from example_libs.mail_service import MailService
            mail_service = MailService()
        self.mail_service = mail_service
        app.add_url_rule('/health', 'health', self.health, methods=['GET'])
        self.app = app

    def health(self):
        result = self.mail_service.check()
        return jsonify(result)

    def create_app(self):
        return self.app

