"""DynamoDB-backed storage for People.

Uses the same boto3 calls locally (against a DynamoDB emulator) and in Cloud
One (against the real table provisioned by template.yaml).
"""
import os
import uuid

import boto3

PEOPLE_TABLE_NAME = os.environ.get("PEOPLE_TABLE_NAME", "master-project-plan-software-development-people-dev")
APPLICATIONS_TABLE_NAME = os.environ.get(
    "APPLICATIONS_TABLE_NAME", "master-project-plan-software-development-applications-dev"
)
PROJECTS_TABLE_NAME = os.environ.get(
    "PROJECTS_TABLE_NAME", "master-project-plan-software-development-projects-dev"
)
DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL")  # local emulator only
AUTO_CREATE_TABLE = os.environ.get("AUTO_CREATE_TABLE", "true").lower() == "true"


def _resource():
    return boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_URL)


def _table(table_name):
    return _resource().Table(table_name)


def ensure_table_exists(table_name):
    """Create the table if missing. Local/test convenience only; the real
    Cloud One tables are provisioned by SAM (AUTO_CREATE_TABLE=false there)."""
    if not AUTO_CREATE_TABLE:
        return
    resource = _resource()
    existing = [t.name for t in resource.tables.all()]
    if table_name in existing:
        return
    table = resource.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()


def seed_if_empty(seed_people):
    if not AUTO_CREATE_TABLE:
        return
    if list_people():
        return
    for person in seed_people:
        create_person(**person)


def list_people():
    items = _table(PEOPLE_TABLE_NAME).scan().get("Items", [])
    items.sort(key=lambda p: (p["last_name"], p["first_name"]))
    return items


def get_person(person_id):
    return _table(PEOPLE_TABLE_NAME).get_item(Key={"id": person_id}).get("Item")


def create_person(first_name, last_name, nih_email):
    person = {
        "id": str(uuid.uuid4()),
        "first_name": first_name,
        "last_name": last_name,
        "nih_email": nih_email,
    }
    _table(PEOPLE_TABLE_NAME).put_item(Item=person)
    return person


def update_person(person_id, first_name, last_name, nih_email):
    _table(PEOPLE_TABLE_NAME).update_item(
        Key={"id": person_id},
        UpdateExpression="SET first_name = :f, last_name = :l, nih_email = :e",
        ExpressionAttributeValues={":f": first_name, ":l": last_name, ":e": nih_email},
    )
    return get_person(person_id)


def delete_person(person_id):
    _table(PEOPLE_TABLE_NAME).delete_item(Key={"id": person_id})


def list_applications():
    items = _table(APPLICATIONS_TABLE_NAME).scan().get("Items", [])
    items.sort(key=lambda a: a["name"].lower())
    return items


def get_application(application_id):
    return _table(APPLICATIONS_TABLE_NAME).get_item(Key={"id": application_id}).get("Item")


def create_application(**fields):
    application = {"id": str(uuid.uuid4()), **fields}
    _table(APPLICATIONS_TABLE_NAME).put_item(Item=application)
    return application


def clear_applications():
    table = _table(APPLICATIONS_TABLE_NAME)
    with table.batch_writer() as batch:
        for item in table.scan().get("Items", []):
            batch.delete_item(Key={"id": item["id"]})


def list_projects():
    items = _table(PROJECTS_TABLE_NAME).scan().get("Items", [])
    items.sort(key=lambda p: p["number"])
    return items


def get_project(project_id):
    return _table(PROJECTS_TABLE_NAME).get_item(Key={"id": project_id}).get("Item")


def create_project(**fields):
    project = {"id": str(uuid.uuid4()), **fields}
    _table(PROJECTS_TABLE_NAME).put_item(Item=project)
    return project


def clear_projects():
    table = _table(PROJECTS_TABLE_NAME)
    with table.batch_writer() as batch:
        for item in table.scan().get("Items", []):
            batch.delete_item(Key={"id": item["id"]})
