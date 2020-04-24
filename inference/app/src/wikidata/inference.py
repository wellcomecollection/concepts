from . import fetch_url_json


async def search_wikidata(query):
    response = await fetch_url_json(
        url="https://www.wikidata.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }
    )
    if response["object"].status != 200:
        raise ValueError(f"Couldn't find '{query}' in Wikidata")

    try:
        wikidata_id = response["json"]["query"]["search"][0]["title"]
    except (KeyError, IndexError):
        raise ValueError(f"Couldn't find '{query}' in Wikidata")
    return wikidata_id