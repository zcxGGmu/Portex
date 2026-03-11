.PHONY: init-db build-agent-runner build-release-image

init-db:
	python scripts/init_db.py

build-release-image:
	python scripts/build_docker.py

build-agent-runner:
	python scripts/build_docker.py --tag portex/agent-runner:dev --file container/agent-runner/Dockerfile --context container/agent-runner
