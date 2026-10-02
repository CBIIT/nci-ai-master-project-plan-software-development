import unittest

from app import app


class RouteTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello, World", response.data)

    def test_health_returns_ok(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


class LambdaHandlerTestCase(unittest.TestCase):
    def _function_url_event(self, path):
        return {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": path,
            "rawQueryString": "",
            "headers": {"host": "example.com"},
            "requestContext": {
                "http": {
                    "method": "GET",
                    "path": path,
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                },
                "domainName": "example.com",
            },
            "isBase64Encoded": False,
        }

    def test_lambda_handler_root(self):
        from function import lambda_handler

        response = lambda_handler(self._function_url_event("/"), None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Hello, World", response["body"])

    def test_lambda_handler_health(self):
        from function import lambda_handler

        response = lambda_handler(self._function_url_event("/health"), None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("ok", response["body"])


if __name__ == "__main__":
    unittest.main()
