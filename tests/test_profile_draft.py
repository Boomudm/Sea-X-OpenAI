"""Draft profiles from scripted Responses API results."""

import json
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from trongpok.errors import InvalidReaderOutput, ReaderInputError
from trongpok.profile_draft import draft_profile
from trongpok.profiles import CategoryProfile, load_profile

SPEC_URL = "https://brand.example/specifications/model"


def profile_payload(**changes):
    return load_profile("storage").model_dump(mode="json") | {
        "category": "test_category",
        "approved_by": "model self-approval",
    } | changes


def api_response(profile, *, opened=(SPEC_URL,), status="completed", search_sources=()):
    search = [{
        "id": "search_sources",
        "type": "web_search_call",
        "status": "completed",
        "action": {"type": "search", "sources": [
            {"type": "url", "url": url} for url in search_sources
        ]},
    }] if search_sources else []
    return {
        "id": "resp_profile",
        "object": "response",
        "created_at": 0,
        "model": "gpt-6.2-sol",
        "status": status,
        "output": search + [
            {
                "id": f"search_{index}",
                "type": "web_search_call",
                "status": "completed",
                "action": {"type": "open_page", "url": url},
            }
            for index, url in enumerate(opened)
        ] + [{
            "id": "message_profile",
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [{
                "type": "output_text",
                "text": json.dumps(profile),
                "annotations": [],
            }],
        }],
    }


def scripted_client(response, *, on_request=None):
    requests = []

    def script(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/responses"
        requests.append(json.loads(request.content))
        if on_request is not None:
            on_request()
        return httpx.Response(200, json=response)

    http = httpx.Client(transport=httpx.MockTransport(script))
    return OpenAI(api_key="scripted", http_client=http, max_retries=0), requests


def test_official_spec_response_creates_a_valid_pending_profile(tmp_path: Path):
    client, requests = scripted_client(api_response(profile_payload()))
    with client:
        path = draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert path == tmp_path / "test_category.json"
    profile = CategoryProfile.model_validate_json(path.read_bytes())
    assert profile.category == "test_category"
    assert profile.approved_by == "pending human review"
    assert profile.official_spec_urls == (SPEC_URL,)

    [request] = requests
    assert request["text"]["format"]["schema"] == CategoryProfile.model_json_schema()
    assert request["tools"] == [{
        "type": "web_search",
        "filters": {"allowed_domains": ["brand.example"]},
    }]
    assert json.loads(request["input"][1]["content"]) == {
        "category": "test_category",
        "official_spec_urls": [SPEC_URL],
    }
    assert request["store"] is False


@pytest.mark.parametrize(("category", "url"), [
    ("../storage", SPEC_URL),
    ("test_category", "file:///private/spec.pdf"),
    ("test_category", "https://localhost/spec"),
    ("test_category", "https://127.0.0.1/spec"),
    ("test_category", "https://user:password@brand.example/spec"),
])
def test_invalid_input_never_calls_responses(tmp_path: Path, category, url):
    client, requests = scripted_client(api_response(profile_payload()))
    with client, pytest.raises(ReaderInputError):
        draft_profile(category, [url], profiles_dir=tmp_path, client=client)

    assert requests == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(("opened", "status"), [((), "completed"), ((SPEC_URL,), "incomplete")])
def test_unverified_spec_response_leaves_no_draft(tmp_path: Path, opened, status):
    client, requests = scripted_client(api_response(profile_payload(), opened=opened, status=status))
    with client, pytest.raises(InvalidReaderOutput, match="open every supplied"):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert len(requests) == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("opened", [
    (),
    ("https://brand.example/specifications/different-model",),
    (SPEC_URL + "?version=old",),
])
def test_search_result_alone_never_counts_as_an_exact_page_open(tmp_path: Path, opened):
    client, requests = scripted_client(api_response(
        profile_payload(), opened=opened, search_sources=(SPEC_URL,),
    ))
    with client, pytest.raises(InvalidReaderOutput, match="open every supplied"):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert len(requests) == 1
    assert list(tmp_path.iterdir()) == []


def test_exact_open_allows_equivalent_host_port_and_fragment(tmp_path: Path):
    client, _ = scripted_client(api_response(profile_payload(), opened=(
        "https://BRAND.example:443/specifications/model#dimensions",
    )))
    with client:
        path = draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert CategoryProfile.model_validate_json(path.read_bytes()).official_spec_urls == (SPEC_URL,)


def test_each_supplied_spec_requires_its_own_completed_open(tmp_path: Path):
    second_url = "https://other.example/products/model/spec"
    response = api_response(profile_payload(), opened=(SPEC_URL, second_url))
    response["output"][1]["status"] = "failed"
    client, _ = scripted_client(response)

    with client, pytest.raises(InvalidReaderOutput, match="open every supplied"):
        draft_profile("test_category", [SPEC_URL, second_url], profiles_dir=tmp_path, client=client)

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("changes", [{"category": "storage"}, {"tolerance": 1.5}])
def test_wrong_category_or_invalid_rules_leave_no_draft(tmp_path: Path, changes):
    client, _ = scripted_client(api_response(profile_payload(**changes)))
    with client, pytest.raises(InvalidReaderOutput, match="valid requested profile"):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert list(tmp_path.iterdir()) == []


def test_existing_approved_profile_survives_before_any_request(tmp_path: Path):
    destination = tmp_path / "test_category.json"
    content = json.dumps(profile_payload(approved_by="Human reviewer"))
    destination.write_text(content, encoding="utf-8")
    client, requests = scripted_client(api_response(profile_payload()))
    with client, pytest.raises(FileExistsError):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert requests == []
    assert destination.read_text(encoding="utf-8") == content


def test_profile_created_during_request_survives_publication(tmp_path: Path):
    destination = tmp_path / "test_category.json"
    content = json.dumps(profile_payload(approved_by="Another reviewer"))
    client, _ = scripted_client(
        api_response(profile_payload()),
        on_request=lambda: destination.write_text(content, encoding="utf-8"),
    )
    with client, pytest.raises(FileExistsError):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert list(tmp_path.iterdir()) == [destination]
    assert destination.read_text(encoding="utf-8") == content


def test_draft_rejects_completed_open_of_an_unexpected_page(tmp_path):
    unexpected = "https://brand.example/specifications/another-model"
    client, _ = scripted_client(api_response(profile_payload(), opened=(SPEC_URL, unexpected)))

    with client, pytest.raises(InvalidReaderOutput, match="only those pages"):
        draft_profile("test_category", [SPEC_URL], profiles_dir=tmp_path, client=client)

    assert list(tmp_path.iterdir()) == []
