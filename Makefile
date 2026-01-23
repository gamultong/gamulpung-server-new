ACT = bin/act
TYPE = dev

.PHONY: act-ci act-cd-dev act-cd-prod

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

profile:
	@if [ -z "$(pfn)" ]; then \
		echo "❌ pfn 파라미터가 필요합니다." \
		exit 1; \
	fi
	uv run python -m tests.profile.${pfn}.profiling

branch-clear:
	git fetch --all --prune
	git branch --merged develop   | egrep -v 'develop'   | xargs -n 1 git branch -d