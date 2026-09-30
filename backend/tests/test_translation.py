import io
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import translation as tr

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('TRANSLATION_DAILY_LIMIT', '300')
    tr._cache.clear()
    tr._requests.clear()


def provider(monkeypatch, response):
    calls = []
    def send(request, timeout):
        calls.append(json.loads(request.data))
        assert timeout == 18
        return io.BytesIO(json.dumps(response).encode())
    monkeypatch.setattr(tr.urllib.request, 'urlopen', send)
    return calls


def complete(text):
    return {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}]}


def test_connected_translation_and_context_sensitive_cache(monkeypatch):
    calls = provider(monkeypatch, complete('to come before you with speeches'))
    payload = {'text': 'λόγους εἰς ὑμᾶς εἰσιέναι.', 'context': 'ὥσπερ μειρακίῳ πλάττοντι λόγους εἰς ὑμᾶς εἰσιέναι.'}
    r = client.post('/api/translate', json=payload)
    assert r.status_code == 200
    assert r.json()['translation'] == 'to come before you with speeches'
    assert calls[0]['store'] is False
    assert json.loads(calls[0]['input']) == {'selected_text': payload['text'], 'surrounding_context': payload['context']}
    assert client.post('/api/translate', json=payload).json() == r.json()
    assert len(calls) == 1
    client.post('/api/translate', json={**payload, 'context': 'Different context'})
    assert len(calls) == 2


def test_missing_key_does_not_break_dictionary(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY')
    assert client.post('/api/translate', json={'text': 'λόγος'}).status_code == 503
    assert client.get('/api/lookup', params={'text': 'λόγος'}).json()['words'][0]['matches']


@pytest.mark.parametrize('response', [{'status': 'incomplete', 'output': []}, {'status': 'completed', 'output': []}])
def test_incomplete_or_empty_response_is_not_cached(monkeypatch, response):
    calls = provider(monkeypatch, response)
    for _ in range(2):
        assert client.post('/api/translate', json={'text': 'λόγος'}).status_code == 503
    assert len(calls) == 2 and not tr._cache


def test_provider_failure_is_sanitized_and_releases_slot(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('private-provider-error test-key')
    monkeypatch.setattr(tr.urllib.request, 'urlopen', fail)
    for _ in range(3):
        r = client.post('/api/translate', json={'text': 'λόγος'})
        assert r.status_code == 503 and 'test-key' not in r.text


def test_limits_before_provider_request(monkeypatch):
    calls = provider(monkeypatch, complete('word'))
    for payload in [{'text': ''}, {'text': 'English only'}, {'text': 'α' * 2001}, {'text': 'λόγος ' * 201}, {'text': 'λόγος', 'context': 'α' * 4001}]:
        assert client.post('/api/translate', json=payload).status_code == 422
    assert not calls
    monkeypatch.setenv('TRANSLATION_DAILY_LIMIT', '1')
    assert client.post('/api/translate', json={'text': 'λόγος'}).status_code == 200
    assert client.post('/api/translate', json={'text': 'ἄνθρωπος'}).status_code == 429
    assert client.post('/api/translate', json={'text': 'λόγος'}).status_code == 200
    assert len(calls) == 1
