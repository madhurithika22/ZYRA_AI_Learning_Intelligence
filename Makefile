.PHONY: web-dev api-dev

web-dev:
	npm --prefix apps/web run dev

api-dev:
	cd apps/api && python -m uvicorn app.main:app --reload