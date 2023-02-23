#!/usr/bin/env python3
import os
import zipfile
import urllib.request
import shutil

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

SCRIPT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))


def path_within_firmware_repo(path):
    return os.path.join(SCRIPT_DIRECTORY, "..", path)


# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url="https://oryx.zsa.io/graphql")

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

# Provide a GraphQL query
query = gql(
    """
    query getLayout($hashId: String!, $revisionId: String!, $geometry: String) {
  Layout(hashId: $hashId, geometry: $geometry, revisionId: $revisionId) {
    ...LayoutData
    __typename
  }
}

fragment LayoutData on Layout {
  title
  revision {
    ...RevisionData
    __typename
  }
  lastRevisionCompiled
  isLatestRevision
  __typename
}

fragment RevisionData on Revision {
  createdAt
  hashId
  model
  title
  zipUrl
  qmkVersion
  qmkUptodate
  __typename
}
"""
)


def download_locally(url, directory_path):
    url_basename = os.path.basename(url)
    file_path = os.path.join(directory_path, url_basename)
    print(f"download_locally saving to {file_path}")
    urllib.request.urlretrieve(url, file_path)
    return file_path


def unzip(zip_path, output_directory_path):
    print(f"unzip {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as fp:
        fp.extractall(output_directory_path)


def infer_source_directory_from_zip_url(zip_url):
    url_basename = os.path.basename(zip_url)
    return url_basename[:-15] + "source"


def sync_directory(source, destination):
    print(f"sync_directory {source} => {destination}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


# Execute the query on the transport
result = client.execute(
    query,
    variable_values={
        "hashId": "lzxz0",
        "geometry": "ergodox-ez",
        "revisionId": "latest",
    },
)
import pprint

pprint.pprint(result)

zip_url = result["Layout"]["revision"]["zipUrl"]
temp_directory = "/tmp/layout/"

local_zip_path = download_locally(zip_url, temp_directory)
unzip(local_zip_path, temp_directory)
source_directory_origin_name = infer_source_directory_from_zip_url(zip_url)
destination_directory_path = path_within_firmware_repo(
    "keyboards/ergodox_ez/shine/keymaps/freevoid_main/"
)

sync_directory(
    os.path.join(temp_directory, source_directory_origin_name),
    destination_directory_path,
)
