---
title: "High value tests with Python Flask"
date: 2019-03-26:11:03+01:00
draft: true
---

# Introduction

After 6 years developing Python Flask applications, mainly REST API's, in 2019 I still could not find good article on developing high value tests for Python Flask based applications. That is going to change today!

First I will give my opinion on testing and methodology followed by a demo case to illustrate high value testing with actual code. Feel free to skip all the boring reading and head directly over to the code on [Github](https://github.com/xiwenc/python-flask-app-testing).

The foundation described in this article is mainly focussed on early projects with limited resources like time and people effort. In these cases you want lowest possible investment with high return in value. Note that this is no silver bullet.

# High value tests
As a software engineer that has built many micro services in the past I have always believed having integration tests in the early stages of a product is of utmost importance to detect issues and confirm assumptions. Nowadays it is rare to build fully self contained systems that does not interact with another external systems. This external system could be a webservice or perhaps a complicated library that renders PDF files.

My definition for "High value tests" is inspired by [High Cost Tests and High Value Tests](https://medium.com/table-xi/high-cost-tests-and-high-value-tests-a86e27a54df):
A test case that is *efficient* and *effective* that focusses on business logic *we* have implemented.

So let's dissect this statement. We want our tests to be *efficient* because it is not funny to wait for hours for a test case to finish to discover it failed. Or it demands many resources like compute power or manual labor which could be very costly. *Effective* because we are only interested in interfacing of third party library or web service but not their inner workings. Finally there is emphasis on *we*. Our system is often a composition of one or more other components working in harmony. Full complexity of systems are in fact all the code you have produced together with the code of all your dependencies and their dependencies. As you might have guessed already in practice systems are often very complicated. As we do not have access to infinite resources we have to get the most out of our investments so we test the interfaces of these external dependencies only.

In practice good test cases are a balance between depth (when do we include external dependencies), simplicity and flexibility.

# Anatomy

Following the [AAA (Arrange, Act and Assert) pattern](http://wiki.c2.com/?ArrangeActAssert) we define the anatomy of a good high value test case to have the follow components:

- **Goal**: Why are we writing this test?
- **Arrange**: What assumptions do we have if any?
- **Act**: Trigger the API endpoint or function call
- **Assert**: Verify expected results

Other non-functional requirements are:
- Simplicity: someone with low programming skills should be able to extend or create new test cases based on existing ones
- Fast: ideally the test case completes in milliseconds
- Readability: conventional programming best practices should be applied to tests also like short but descriptive variable names

# Example: Simple REST API with Flask

Let's consider a simple Flask app that uses a hypothetical mail service implemented as `MailService`. Below is the file and directory structure of our application with 4 test cases implemented in 2 files (`test_errors.py` and `test_health.py`). We will dive deeper into the code in the rest of this section.

```
├── README.md
├── app
│   ├── __init__.py
│   └── main.py
├── example_libs
│   ├── __init__.py
│   └── mail_service.py
├── requirements.txt
└── tests
    ├── __init__.py
    ├── base.py
    ├── test_errors.py
    └── test_health.py
```

In the app we have defined two REST endpoints:
* GET /health: responsible for reporting the health status of our app. The app's health is partly determined by whether we can communicate with the mail service. We do this by calling the `check()` method on the mail service instance. 
* PUT /error: throws a generic `Exception` simulating a runtime error.

Here's actual source code `main.py`:

```python
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

        @app.route("/throw-exception", methods=["PUT"])
        def error():
            raise Exception("An error has occurred")

        return app

if __name__ == "__main__":
    App().create_app().run()
```

## Test suite overview

Test cases are often located in the `tests` directory. Each test case is implemented as a TestCase class. Below class diagram depicts the high level composition of such TestCase. 

```plantuml

abstract class AAAMixin {
    {abstract} app ARRANGE()
    {abstract} void ACT()
    {abstract} void ASSERT()
    void test_case()
    - app create_app()
}
class LiveServerTestCase {
    {abstract} app create_app()
    ...
}
class TestCase {
    ARRANGE()
    ACT()
    ASSERT()
}

AAAMixin <|-- TestCase
LiveServerTestCase <|-- TestCase
```


## AAAMixin

Before we start writing our test cases we first define our `AAAMixin` class which implements a basic structure according to the AAA methodology discussed earlier. We will use this mixin class later in our test cases. To void the `assert` keyword we write the main AAA methods which must be implemented by all test cases: `ARRANGE()`, `ACT()` and `ASSERT()`.

```python
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
```

The `AAAMixin` class is tightly coupled with the `LiveServerTestCase` class. Therefore the flow of execution differs a bit than conventional test cases. The following methods are executed in this order:
* `create_app()`: returns the app created by `ARRANGE()`. This is needed because LiveServerTestCase expects this method to be implemented.
  * `ARRANGE()`: to create the app, mocking if any have to be done in here
* `setUp()`: extra setup steps, here we pre-create the `test_client`
* `test_case()`: impliciet test case. This is comparable to `main()` as main entry point but this is our test case and all test cases must start with `test_` prefix.
  * `ACT()`: make call to API using `self.client` and return its response to `self.response`.
  * `ASSERT()`: verify expected results by accessing `self.response`.

If we disregard non AAA related methods we will see that the AAAMixin forces us to stick to the AAA pattern. It is therefore sufficient for us to implement just these 3 methods to compose our test case.

## Integration test: /health

With the `AAAMixin` defined we can combine it with `LiveServerTestCase` from `flask_testing` package to write our first test case for `GET /health`. This test shows how we can use the AAA approach with a live server instance of our app to test against a real `MailService` instance.

```python
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
```

## Unit test: /health

In a real world scenario the MailService could slow down our test. We could have a very limited set of integration tests of this service and mock it most of the time. Mocking is very useful because it's fast and that's were we set our boundaries of where we stop testing logic that was not implemented by us (with the assumption the third party library is well tested on its own).

```python
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
```

## More test cases

To illustrate how easy and obvious it is to create more test cases we have implemented 2 more test cases to test for errors.

```python
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
        return self.client.put("/error")

    def ASSERT(self):
        assert self.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
```

# Demo

Enough text, lets see how all of this works:

```bash
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r test-requirements.txt
python -m pytest ./tests -vv
```

Example output:
```
================================================ test session starts =================================================
platform darwin -- Python 3.7.2, pytest-4.4.0, py-1.8.0, pluggy-0.9.0 -- /Users/xcheng/private/git/flask-app-testing/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/xcheng/private/git/flask-app-testing
collected 4 items

tests/test_errors.py::TestErrors_not_found::test_case <- tests/base.py PASSED                                  [ 25%]
tests/test_errors.py::TestErrors_throw_exception::test_case <- tests/base.py PASSED                            [ 50%]
tests/test_health.py::TestHealth_sick::test_case <- tests/base.py PASSED                                       [ 75%]
tests/test_health.py::TestHealth_integration::test_case <- tests/base.py PASSED                                [100%]

================================================== warnings summary ==================================================
venv/lib/python3.7/site-packages/jinja2/utils.py:485
  /Users/xcheng/private/git/flask-app-testing/venv/lib/python3.7/site-packages/jinja2/utils.py:485: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
    from collections import MutableMapping

venv/lib/python3.7/site-packages/jinja2/runtime.py:318
  /Users/xcheng/private/git/flask-app-testing/venv/lib/python3.7/site-packages/jinja2/runtime.py:318: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
    from collections import Mapping

-- Docs: https://docs.pytest.org/en/latest/warnings.html
======================================== 4 passed, 2 warnings in 0.78 seconds ========================================
```

# Evaluation

Our final test cases adhere to:
- AAA principles: explicit arrange, act & assert; nothing else
- simplicity: implement 3 methods and your are good to go
- fast: runs in milliseconds and allows easy mocking of components 
- readable: the structure is easy to understand

With the ability of running our tests againt a live server over HTTP allows us to test our API's more in depth. And we have the choice to decide how deep because of the easiness of mocking pieces of our application. For this to work our `App.create_app()` must be able to accept instances to be mocked. Alternatively one could explore the possibility to do monkey patching.

# Conclusions

This test suite is currently being used by a medium sized Python REST API service. It has speeded up our development significantly and onboarding new developers was a breeze.

Checkout the code on [Github](https://github.com/xiwenc/python-flask-app-testing)


# Future

In the future we will extend this simple REST API with MySQL database support. In the light of high value tests we will also extend the test suite with support for launching MySQL service to support our tests.
As our test suite grows, there will be demand for parallelization.

# References

- https://medium.com/@hakibenita/keeping-tests-dry-with-class-based-tests-in-python-e3f2d815124
- https://medium.com/table-xi/high-cost-tests-and-high-value-tests-a86e27a54df
- http://wiki.c2.com/?ArrangeActAssert
- http://softwaretestingfundamentals.com/unit-testing/
- https://techbeacon.com/devops/6-best-practices-integration-testing-continuous-integration
- https://hackernoon.com/low-effort-high-value-integration-tests-in-redux-apps-d3a590bd9fd5
- https://dev.to/lgraziani2712/the-value-of-unit-or-integration-testing-56i0
