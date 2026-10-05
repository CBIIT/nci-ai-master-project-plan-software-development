# MasterProjectPlan-SoftwareDevelopment

A minimal NCI Hello, World Flask web application, created as the local
baseline for this project before real development begins.

## Run locally

This app stores People and Applications in DynamoDB, so local development
needs a local DynamoDB instance. Use the official DynamoDB Local (persists
to disk, unlike moto's in-memory mock), downloaded once to
`~/.local/dynamodb-local`:

```bash
# one-time setup
brew install openjdk
mkdir -p ~/.local/dynamodb-local && cd ~/.local/dynamodb-local
curl -fL https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz \
  -o dynamodb_local_latest.tar.gz && tar -xzf dynamodb_local_latest.tar.gz
```

Each time you develop, in one terminal start DynamoDB Local (data persists
in `.dynamodb-data/` across restarts):

```bash
cd ~/.local/dynamodb-local
/opt/homebrew/opt/openjdk/bin/java -Djava.library.path=./DynamoDBLocal_lib \
  -jar DynamoDBLocal.jar -port 8000 \
  -dbPath /path/to/this/repo/.dynamodb-data -sharedDb
```

In another terminal, run the app pointed at it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing AWS_DEFAULT_REGION=us-east-1 \
  DYNAMODB_ENDPOINT_URL=http://127.0.0.1:8000 python3 app.py
```

Then open http://127.0.0.1:5000/ in a browser.

## Health check

`GET /health` returns `{"status": "ok"}`.

## Registry

Registered in the [NCI Skills Registry](https://github.com/CBIIT/NCI-Skills-Registry)
as `master-project-plan-software-development`.
