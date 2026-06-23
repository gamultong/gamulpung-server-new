# act 바이너리는 https://github.com/nektos/act 릴리스에서 받아 bin/에 둔다 (git 미추적)
ENV_FILE := .env
RUNTIME_TARGETS := dev run check-port
REQUESTED_TARGETS := $(if $(MAKECMDGOALS),$(MAKECMDGOALS),dev)
NEEDS_RUNTIME_ENV := $(filter $(RUNTIME_TARGETS),$(REQUESTED_TARGETS))

ifneq ($(wildcard $(ENV_FILE)),)
include $(ENV_FILE)
export
endif

ifneq ($(NEEDS_RUNTIME_ENV),)
ifeq ($(wildcard $(ENV_FILE)),)
$(error $(ENV_FILE) file is required)
endif

PORT_DEFINED_IN_ENV := $(shell awk -F= '/^[[:space:]]*(export[[:space:]]+)?PORT[[:space:]]*=/ { print "1"; exit }' $(ENV_FILE))
ifeq ($(PORT_DEFINED_IN_ENV),)
$(error PORT is required in $(ENV_FILE))
endif

ifeq ($(strip $(PORT)),)
$(error PORT is required in $(ENV_FILE))
endif
endif

ACT = bin/act
TYPE = dev
HOST ?= 0.0.0.0

.PHONY: dev run check-port up deploy act-ci act-cd-dev act-cd-prod test-all profile branch-clear

dev: check-port
	@echo "Starting dev server on $(HOST):$(PORT)"
	uv run python -c "from server import app; from receiver import *; import uvicorn; uvicorn.run(app, host='$(HOST)', port=$(PORT))"

run: dev

check-port:
	@if command -v lsof >/dev/null 2>&1; then \
		if lsof -iTCP:$(PORT) -sTCP:LISTEN -Pn >/dev/null; then \
			echo "ERROR: port $(PORT) is already in use."; \
			lsof -iTCP:$(PORT) -sTCP:LISTEN -Pn; \
			exit 1; \
		fi; \
	fi

up:
	bash scripts/deploy/main.sh

deploy: up

## CI workflow 로컬 테스트
act-ci:
	$(ACT) pull_request -W .github/workflows/CI.yml \
		--secret-file .secrets/$(TYPE).env

## CD-dev workflow 로컬 테스트
act-cd-dev:
	@cat .secrets/.secrets .secrets/dev.env > /tmp/act-dev.secrets
	$(ACT) push -W .github/workflows/CD-dev.yml \
		--secret-file /tmp/act-dev.secrets
	@rm /tmp/act-dev.secrets

## CD-prod workflow 로컬 테스트
act-cd-prod:
	@cat .secrets/.secrets .secrets/prod.env > /tmp/act-prod.secrets
	$(ACT) push -W .github/workflows/CD-prod.yml \
		--secret-file /tmp/act-prod.secrets
	@rm /tmp/act-prod.secrets


test-all:
	uv run pytest

lint:
	uv run ruff check .

profile:
	@if [ -z "$(pfn)" ]; then \
		echo "❌ pfn 파라미터가 필요합니다."; \
		exit 1; \
	fi
	uv run python -m tests.profile.${pfn}.profiling

branch-clear:
	git fetch --all --prune
	git branch --merged develop   | egrep -v 'develop'   | xargs -n 1 git branch -d
