SHELL := /bin/bash

DEFAULT_MODE := git
MODE ?= $(DEFAULT_MODE)

.DEFAULT_GOAL := help

local:
	poetry run python -m spacy download en_core_web_md && poetry run python -m debugpy --listen 0.0.0.0:5690 -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload --reload-dir ./ --reload-dir ../base-tdb-models --reload-dir ../base-tdb-clients --reload-dir ../base-tdb-helpers

sync:
	@echo "🔄 Running sync_git_deps.py with mode: $(MODE)"
	python sync_git_deps.py --mode "$(MODE)"

sync-dry-run:
	@echo "🔍 Dry-run sync for validation (mode: $(MODE))"
	python sync_git_deps.py --mode "$(MODE)" --dry-run

install-hooks:
	@echo "Installing git hooks..."
	@cp -f git-hooks/* .git/hooks/
	@chmod +x .git/hooks/*
	@echo "Git hooks installed!"

docker-publish:
	@bash docker-publish.sh

help:
	@echo ""
	@echo "Targets:"
	@echo "  make local   → start local stack"
	@echo "  make sync MODE=<git|local>      → sync git deps (default: git)"
	@echo "  make sync-dry-run MODE=<git|local> → validate deps without changing files"
	@echo "  install-hooks → install git hooks"
	@echo ""
