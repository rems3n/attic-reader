import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import router, COOKIE

@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'users.db'))
    app = FastAPI()
    app.include_router(router)
    return [TestClient(app, base_url='https://testserver', headers={'X-Attic-Request':'1'}) for _ in range(2)]

def signup(c, email='learner@example.com'):
    return c.post('/api/auth/signup', json={'email':email, 'password':'long test password 123'})

def document():
    return {'version':2, 'cards':{}, 'settings':{}, 'course':{'lessons':{'1.1':{'status':'done'}}}, 'log':[]}

def test_signup_login_logout_and_cookie(clients):
    a, b = clients
    r = signup(a)
    assert r.status_code == 200
    cookie = r.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie
    assert a.get('/api/me').json()['user']['email'] == 'learner@example.com'
    assert a.get('/api/me').headers['cache-control'] == 'no-store'
    assert b.get('/api/me').status_code == 401
    assert b.post('/api/auth/login', json={'email':'learner@example.com','password':'wrong'}).status_code == 401
    assert b.post('/api/auth/login', json={'email':'LEARNER@example.com','password':'long test password 123'}).status_code == 200
    old = a.cookies.get(COOKIE)
    assert a.post('/api/auth/logout').status_code == 200
    a.cookies.set(COOKIE, old)
    assert a.get('/api/me').status_code == 401

def test_isolation_revision_and_account_switch(clients):
    a, b = clients
    user = signup(a).json()['user']
    signup(b, 'other@example.com')
    assert a.put('/api/me/progress', json={'revision':0,'document':document()}).status_code == 200
    assert a.get('/api/me/progress').json()['document'] == document()
    assert b.get('/api/me/progress').json()['document'] is None
    assert a.put('/api/me/progress', json={'revision':0,'document':document()}).status_code == 409
    assert b.put('/api/me/progress', headers={'X-Attic-User':user['id']}, json={'revision':0,'document':document()}).status_code == 409
    assert a.put('/api/me/progress', json={'revision':1,'document':document()}).json()['revision'] == 2

def test_validation_csrf_and_limits(clients):
    a, b = clients
    assert a.post('/api/auth/signup', json={'email':'bad','password':'short'}).status_code == 422
    assert a.post('/api/auth/signup', headers={'Origin':'https://evil.example'}, json={'email':'ok@example.com','password':'long test password'}).status_code == 403
    a.headers.pop('X-Attic-Request')
    assert signup(a).status_code == 403
    for _ in range(15):
        assert b.post('/api/auth/login',json={'email':'limit@example.com','password':'wrong'}).status_code == 401
    assert b.post('/api/auth/login',json={'email':'limit@example.com','password':'wrong'}).status_code == 429
