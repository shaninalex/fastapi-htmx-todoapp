start:
	@uvicorn main:app --reload

format:
	@black *.py
	@black **/*.py
