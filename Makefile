.PHONY: setup test demo dashboard refresh verify

setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/pip install -e .

refresh:
	python -m fixed_income_risk.cli refresh

demo:
	python -m fixed_income_risk.cli demo

dashboard:
	streamlit run dashboard/app.py

test:
	python -m pytest -q

verify: test
	python scripts/verify_project.py
