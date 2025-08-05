# Contributing to draftkid

Thanks for your interest! This project aims to stay simple, reproducible, and open.

## Ways to contribute
- Bug reports and reproducible test cases
- Docs improvements (README, examples)
- New features behind flags (keep nfl_data_py-only by default)

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Coding guidelines
- Python 3.11+
- Small, composable functions
- Add/extend tests for new logic
- No secrets or paid data in the repo

## Pull requests
- Create a feature branch: `git checkout -b feat/<short-name>`
- Include a clear description (what/why/how)
- Link any related issues
