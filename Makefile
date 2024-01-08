run:
	@docker compose up -d --build

start:
	@uvicorn main:app --reload

format:
	@black *.py
	@black **/*.py