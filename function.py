"""Lambda entrypoint wrapping the Flask app for Function URL invocation."""
from apig_wsgi import make_lambda_handler

from app import app

lambda_handler = make_lambda_handler(app)
