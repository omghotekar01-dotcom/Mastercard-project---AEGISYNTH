.PHONY: test api

test:
	cd backend && PYTHONPATH=. pytest -q

api:
	cd backend && uvicorn app.main:app --reload
