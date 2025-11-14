# EVENT = push
ACT = bin/act

.PHONY: act-all act-job act-wf

## 전체 GitHub Actions 로컬 실행 (해당 EVENT 기준)
act-all:
	$(ACT) $(EVENT)

## 특정 workflow 파일만 실행 (예: make act-wf WF=.github/workflows/ci.yml)
act-wf:
	@if [ -z "$(WF)" ]; then \
		echo "❌ WF 파라미터가 필요합니다. 예: make act-wf WF=.github/workflows/ci.yml"; \
		exit 1; \
	fi
	$(ACT) $(EVENT) -W .github/workflows/$(WF).yml