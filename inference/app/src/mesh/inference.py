import logging
from urllib.parse import quote

from . import fetch_url_json
from .exact import get_mesh_data

log = logging.getLogger(__name__)


async def search_mesh(query):
    response = await fetch_url_json(
        url="https://meshb.nlm.nih.gov/api/search/record",
        params={
            "searchInField": "allTerms",
            "sort": "",
            "size": 20,
            "searchType": "allWords",
            "searchMethod": "FullWord",
            "q": quote(query),
        }
    )

    if response["object"].status != 200:
        raise ValueError(f"Couldn't find '{query}' in MeSH")
    try:
        mesh_id = response["json"]["hits"]["hits"][0]["_id"]
    except (KeyError, IndexError):
        raise ValueError(f"Couldn't find '{query}' in MeSH")
    log.info(f"Matched query: '{query}' to MeSH ID: {mesh_id}")

    return mesh_id
