class AAAMixin(object):
    """ Arrange, Act and Assert pattern """

    response = None
    client = None

    def setUp(self):
        """ Called after self.create_app() """
        self.client = self.app.test_client()
        return super().setUp()

    def ARRANGE(self):
        raise NotImplementedError()

    def ACT(self):
        """ Use make call to live server and return the response

        e.g. return self.client.get("/health")
        """
        raise NotImplementedError()

    # assert is a served keyword
    def ASSERT(self):
        raise NotImplementedError()

    def create_app(self):
        return self.ARRANGE()

    def test_case(self):
        """ Single test case per test class """

        # Commented out because it is called by create_app(...) very early
        #self._arrange()
        self.response = self.ACT()
        self.ASSERT()
