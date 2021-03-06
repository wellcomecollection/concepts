import asyncio
import os
import time

from weco_datascience.logging import get_logger
from weco_datascience.http import fetch_url_json

log = get_logger(__name__)


async def get_api_response(url):
    try:
        response = await fetch_url_json(url + ".json")
    except ValueError as e:
        raise e
    if response["object"].status == 200:
        pass
    elif response["object"].status == 404:
        loc_id = os.path.basename(url)
        raise ValueError(f"{loc_id} is not a valid library of congress ID")
    else:
        raise ValueError(
            f"something unexpected happened when calling url: {url}"
        )

    for element in response["json"]:
        if element["@id"] == url:
            return element


def get_wikidata_id(api_response):
    loc_id = os.path.basename(api_response["@id"])

    try:
        wikidata_id = [
            os.path.basename(entity["@id"])
            for entity in api_response[
                "http://www.loc.gov/mads/rdf/v1#hasCloseExternalAuthority"
            ]
            if entity["@id"].startswith("http://www.wikidata.org/entity")
        ][0]
        return wikidata_id
    except (KeyError, IndexError):
        raise ValueError(f"Couldn't find a wikidata ID for LoC ID: {loc_id}")


def get_variants(api_response):
    try:
        variants = [
            altlabel["@value"]
            for altlabel in api_response[
                "http://www.w3.org/2004/02/skos/core#altLabel"
            ]
        ]
    except KeyError:
        loc_id = os.path.basename(api_response["@id"])
        log.debug(f"Couldn't find variants for ID: {loc_id}")
        variants = []
    return variants


def get_label(api_response):
    try:
        label = api_response[
            "http://www.loc.gov/mads/rdf/v1#authoritativeLabel"
        ][0]["@value"]
    except (KeyError, IndexError):
        loc_id = os.path.basename(api_response["@id"])
        log.debug(f"Couldn't find label for ID: {loc_id}")
        label = None
    return label


async def get_hierarchical_concepts(api_response, direction):
    start_time = time.time()
    loc_id = os.path.basename(api_response["@id"])
    response_element_id = (
        f"http://www.loc.gov/mads/rdf/v1#has{direction}Authority"
    )
    try:
        elements = api_response[response_element_id]
    except KeyError:
        log.debug(
            f"Couldn't find {direction.lower()} concepts for ID: {loc_id}"
        )
        return None

    responses = await asyncio.gather(
        *[get_api_response(element["@id"]) for element in elements]
    )

    concepts = [get_label(response) for response in responses]

    log.debug(
        f"Got {direction.lower()} concepts for ID: {loc_id}"
        f", which took took {round(time.time() - start_time, 2)}s"
    )

    return concepts


async def get_lc_subjects_data(loc_id):
    url = f"http://id.loc.gov/authorities/subjects/{loc_id}"
    api_response = await get_api_response(url)

    label = get_label(api_response)
    variants = get_variants(api_response)
    broader_concepts = await get_hierarchical_concepts(api_response, "Broader")
    narrower_concepts = await get_hierarchical_concepts(
        api_response, "Narrower"
    )

    log.debug(f"Got data from lc_subjects for ID: {loc_id}")
    return {
        "id": loc_id,
        "title": label,
        "variants": variants,
        "broader_concepts": broader_concepts,
        "narrower_concepts": narrower_concepts,
    }


async def get_lc_names_data(loc_id):
    url = f"http://id.loc.gov/authorities/names/{loc_id}"
    api_response = await get_api_response(url)
    label = get_label(api_response)
    variants = get_variants(api_response)

    log.debug(f"Got data from lc_names for ID: {loc_id}")

    return {"id": loc_id, "title": label, "variants": variants}
