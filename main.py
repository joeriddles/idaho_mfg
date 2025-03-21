# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4<5",
#   "nats-py[nkeys]<3",
#   "requests<3",
# ]
# ///
from __future__ import annotations

import asyncio
import concurrent.futures
import dataclasses
import functools
import json
import os
import re
import sys
import urllib.parse
from typing import Any, Generator

import nats
import requests
import requests.utils
from bs4 import BeautifulSoup, Tag
from nats.js.api import KeyValueConfig
from nats.js.errors import (
    APIError,
    BucketNotFoundError,
    KeyWrongLastSequenceError,
    NoStreamResponseError,
)

BASE_URL = "https://connect.idmfg.org"
SEARCH_URL = BASE_URL + "/simple-search"


@dataclasses.dataclass
class Company:
    name: str
    email: str
    phone_number: str
    address: str
    website: str
    products_manufactured: str
    detail_url: str


def cache(f):
    """Cache the HTTP response to disk if it is successful."""
    if not os.path.exists(".cache"):
        os.mkdir(".cache")

    @functools.wraps(f)
    def wrapper(_method: str, url: str, **kwargs):
        params = kwargs.get("params", {})
        query_string = urllib.parse.urlencode(params)
        encoded_url = f"{url}?{query_string}".casefold().replace(" ", "_")
        encoded_url = urllib.parse.quote(encoded_url, safe="")
        filepath = f".cache/{_method}_{encoded_url}"
        if os.path.exists(filepath):
            with open(filepath, "rb") as fin:
                response = requests.Response()
                # TODO(joeriddles): handle this better... versioning, more fields, etc.
                response.status_code = int(fin.readline().decode())
                response._content = fin.read()
                return response

        if fail_http:
            raise ValueError("fail_http is true and a request was attempted")

        response = requests.get(url, **kwargs)
        if response.ok:
            with open(filepath, "wb") as fout:
                fout.writelines([f"{response.status_code}\n".encode()])
                fout.write(response.content)
        return response

    return wrapper


@cache
def request(method: str, url: str, **kwargs):
    return requests.request(method, url, **kwargs)


def get(url: str):
    return request("GET", url)


# bs4 helpers
def _get_text(tag: Tag, strip=True) -> str:
    return tag.get_text(strip=strip).replace("\u00a0", " ")


def _must_find(tag: Tag, element: str | None = None, **kwargs) -> Tag:
    result = tag.find(element, **kwargs)
    if result and isinstance(result, Tag):
        return result
    raise ValueError("could not find element")


def _must_find_next(tag: Tag, element: str | None = None, **kwargs) -> Tag:
    result = tag.find_next(element, **kwargs)
    if result and isinstance(result, Tag):
        return result
    raise ValueError("could not find elemenht")


def _must_find_all(
    tag: Tag, element: str | None = None, **kwargs
) -> Generator[Tag, None, None]:
    results = tag.find_all(element, **kwargs)
    for result in results:
        if result and isinstance(result, Tag):
            yield result


def _find_text_after_icon(tag: Tag, icon_title: str, strip=True) -> str:
    try:
        icon = _must_find(tag, "i", title=icon_title)
        if icon.parent:
            return _get_text(icon.parent, strip=strip)
        return ""
    except ValueError:
        text = ""
    return text


def parse_companies(html) -> Generator[Company, None, None]:
    """Parse the HTML body for company details."""

    soup = BeautifulSoup(html, "html.parser")
    view_content = _must_find(soup, "div", class_="view-content")
    rows = _must_find_all(view_content, "div", class_="views-row")
    for row in rows:
        company_name = _get_text(_must_find(row, "span", class_="h4"))
        details = _must_find(row, "div", class_="d-sm-flex")
        email = _find_text_after_icon(details, "Email")
        phone_number = _find_text_after_icon(details, "Phone")
        address = _find_text_after_icon(details, "Address", strip=False).replace(
            "\n      ", ", "
        )
        try:
            icon = _must_find(details, "i", class_="fas fa-globe")
            website = str(_must_find_next(icon).attrs["href"])
        except ValueError:
            website = ""

        try:
            products_header = _must_find(details, "h5")
            products_manufactured = _get_text(_must_find_next(products_header, "p"))
        except ValueError:
            products_manufactured = ""

        details_url = BASE_URL + str(
            _must_find(row, "a", class_="btn btn-sm btn-primary")["href"]
        )

        yield Company(
            company_name,
            email,
            phone_number,
            address,
            website,
            products_manufactured,
            details_url,
        )


KEY_REGEX = re.compile(r"[ /]")
NATS_KEY_INVALID_CHARS_REGEX = re.compile(r"[^A-Za-z0-9-_]")


def parse_company_details(html) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    summary = _must_find(soup, "div", id="summary")
    details = {}
    for table in _must_find_all(summary, "table"):
        for row in _must_find_all(table, "tr"):
            td1 = _must_find_next(row, "td")
            key = _get_text(td1).casefold().replace(":", "")
            key = re.sub(KEY_REGEX, "_", key)
            td2 = _must_find_next(td1, "td")
            value = _get_text(td2)
            details[key] = value
    return details


def has_next(html) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    try:
        link = _must_find(soup, "a", class_="page-link", rel="next")
        query_params = str(link["href"])
        return SEARCH_URL + query_params
    except ValueError:
        return None


def scrape_parallel(
    urls: list[str], max_workers: int = 5
) -> Generator[tuple[str, requests.Response], None, None]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(get, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            yield (url, future.result())


async def scrape():
    # Load all the responses first, then start parsing them, in case parsing blows up
    url = f"{SEARCH_URL}?searchterm=&page=1"
    responses: list[requests.Response] = []
    response = get(url)
    responses.append(response)
    # currently there are 33 pages, loading sequentially is fine
    while next_url := has_next(response.content):
        response = get(next_url)
        responses.append(response)

    companies: list[Company] = []
    company_by_detail_url: dict[str, Company] = {}
    detail_urls: list[str] = []
    for response in responses:
        for company in parse_companies(response.content.decode()):
            companies.append(company)
            detail_urls.append(company.detail_url)
            company_by_detail_url[company.detail_url] = company

    fs = JsonFileSaver("./data")
    companies_dicts = [dataclasses.asdict(company) for company in companies]
    await fs.save("_companies.json", companies_dicts)

    companies_and_details: list[tuple[Company, dict[str, str]]] = []
    for url, detail_response in scrape_parallel(detail_urls):
        company = company_by_detail_url[url]
        filename = re.sub(NATS_KEY_INVALID_CHARS_REGEX, "_", company.name) + ".json"
        details = parse_company_details(detail_response.content)
        companies_and_details.append((company, details))
        await fs.save(filename, details)

    # One key to rule them all
    everything = []
    for company, details in companies_and_details:
        company_dict = dataclasses.asdict(company)
        company_dict["details"] = details
        everything.append(company_dict)

    await fs.save("_everything.json", everything)

    if use_nats:
        ns = NatsSaver("IDAHO_MFG")
        async with ns:
            await ns.save("companies", json.dumps(companies_dicts).encode())

            for company, details in companies_and_details:
                key = "details." + re.sub(
                    NATS_KEY_INVALID_CHARS_REGEX, "_", company.name
                )
                value = json.dumps(details).encode()
                await ns.save(key, value)

            await ns.save("everything", json.dumps(everything).encode())


class FileSaver:
    def __init__(self, folder: str):
        self._folder = folder

        if not os.path.exists(self._folder):
            os.mkdir(self._folder)

    async def save(self, key: str, value: bytes):
        with open(os.path.join(self._folder, key), "wb") as fout:
            fout.write(value)


class JsonFileSaver(FileSaver):
    async def save(self, key: str, value: Any):
        if not isinstance(value, bytes):
            value = json.dumps(value, indent=2).encode()
        await super().save(key, value)


class NatsSaver:
    def __init__(self, kv_name: str):
        self._kv_name = kv_name

    async def __aenter__(self):
        await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._nc.close()

        if exc_type is not None:
            print(exc_type)
            print(exc_val)
            return True
        return False

    async def connect(self):
        server = os.environ.get("NATS_SERVER", "localhost")
        creds = os.environ.get("NATS_CREDS_FILE", None)

        self._nc = await nats.connect(server, user_credentials=creds)
        self._js = self._nc.jetstream()
        try:
            self._kv = await self._js.key_value(self._kv_name)
        except BucketNotFoundError:
            await self._js.create_key_value(KeyValueConfig(self._kv_name))
            self._kv = await self._js.key_value(self._kv_name)

    async def save(self, key: str, value: bytes):
        try:
            seq = await self._kv.create(key, value)
        except KeyWrongLastSequenceError:
            try:
                entry = await self._kv.get(key)
                seq = await self._kv.update(key, value, entry.revision)
            except (APIError, NoStreamResponseError) as err:
                # TODO: refactor this nested exception handling
                print(err)
                raise err
            else:
                print(seq)
        except (APIError, NoStreamResponseError) as err:
            print(err)
            raise err


# global args
fail_http = False
use_files = True
use_nats = False


async def main():
    await scrape()


if __name__ == "__main__":
    fail_http = "--http-fail" in sys.argv
    use_nats = "--nats" in sys.argv
    asyncio.run(main())
