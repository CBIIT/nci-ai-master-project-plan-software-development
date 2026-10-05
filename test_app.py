import os
import unittest

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from moto import mock_aws

_dynamodb_mock = mock_aws()
_dynamodb_mock.start()

from app import app  # noqa: E402  (import after the DynamoDB mock is active)


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

    def test_people_index_lists_seeded_people(self):
        response = self.client.get("/people")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Jordan", response.data)

    def test_people_add_then_view(self):
        response = self.client.post(
            "/people/new",
            data={"first_name": "Ada", "last_name": "Lovelace", "nih_email": "ada@nih.gov"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ada", response.data)
        self.assertIn(b"ada@nih.gov", response.data)

    def test_people_edit_then_delete(self):
        create = self.client.post(
            "/people/new",
            data={"first_name": "Grace", "last_name": "Hopper", "nih_email": "grace@nih.gov"},
        )
        person_id = create.headers["Location"].rsplit("/", 1)[-1]

        edited = self.client.post(
            f"/people/{person_id}/edit",
            data={"first_name": "Grace", "last_name": "Hopper-Murray", "nih_email": "grace@nih.gov"},
            follow_redirects=True,
        )
        self.assertIn(b"Hopper-Murray", edited.data)

        deleted = self.client.post(f"/people/{person_id}/delete", follow_redirects=True)
        self.assertEqual(deleted.status_code, 200)
        self.assertNotIn(b"Hopper-Murray", deleted.data)

    def test_applications_index_empty_by_default(self):
        response = self.client.get("/applications")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Select an application", response.data)

    def test_applications_view_unknown_id_404s(self):
        response = self.client.get("/applications/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_applications_view_shows_created_application(self):
        import db

        application = db.create_application(name="Test App", description="A test application")
        response = self.client.get(f"/applications/{application['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test App", response.data)
        self.assertIn(b"A test application", response.data)



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
