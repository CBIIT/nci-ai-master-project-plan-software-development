from datetime import date

from flask import Flask, render_template

app = Flask(__name__)

PROGRAM_NAME = "MasterProjectPlan-BusinessLane"
AUTHOR_NAME = "Lawrence Brem"
PUBLISHED_DATE = date.today().isoformat()
VERSION = "0.1.0"
ENVIRONMENT = "Local"
DESCRIPTION = "A minimal NCI web application starter"


@app.route("/")
def index():
    return render_template(
        "index.html",
        program_name=PROGRAM_NAME,
        author_name=AUTHOR_NAME,
        published_date=PUBLISHED_DATE,
        version=VERSION,
        environment=ENVIRONMENT,
        description=DESCRIPTION,
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
