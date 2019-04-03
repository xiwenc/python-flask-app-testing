from flask import request, jsonify
from flask import Flask


class App(object):

    def __init__(self, mail_service=None):

        # Create real service if not mocking
        if not mail_service:
            from example_libs.mail_service import MailService
            mail_service = MailService()
        self.mail_service = mail_service

    def create_app(self):
        app = Flask(__name__)
        app.app_context().push()

        @app.route("/health", methods=["GET"])
        def health():
            mail_service_health = self.mail_service.check()
            summary = {
                "mail_service": mail_service_health,
            }
            return jsonify(summary)

        @app.route("/error", methods=["PUT"])
        def error():
            raise Exception("An error has occurred")

        return app

if __name__ == "__main__":
    App().create_app().run()