.PHONY: init-db build-agent-runner

init-db:
	python scripts/init_db.py

build-agent-runner:
	python scripts/build_docker.py
