.PHONY: test backend backend-mms frontend status

test:
	cd backend && pytest -q

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

backend-mms:
	cd backend && python -m pip install -e '.[mms,dev]'

frontend:
	cd frontend && npm run dev

status:
	@curl -s http://localhost:8000/api/tts/status || true
	@printf '\n'
