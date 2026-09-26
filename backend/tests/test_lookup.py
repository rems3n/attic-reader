import unicodedata
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_inflection_and_unicode():
    for word in ['ἀνθρώπου', unicodedata.normalize('NFD', 'ἀνθρώπου')]:
        response = client.get('/api/lookup', params={'text': word})
        assert response.status_code == 200
        matches = response.json()['words'][0]['matches']
        assert any(m['lemma'] == 'ἄνθρωπος' and m['definition'] for m in matches)


def test_phrase_unknown_and_ambiguity():
    words = client.get('/api/lookup', params={'text': 'τίς λόγος ζζζζζ'}).json()['words']
    assert len(words) == 3
    assert words[0]['matches']
    assert any(m['lemma'] == 'λόγος' for m in words[1]['matches'])
    assert words[2]['matches'] == []


def test_selection_limits():
    for text in ['', 'English only', 'α' * 241, 'λόγος ' * 13]:
        assert client.get('/api/lookup', params={'text': text}).status_code == 422
