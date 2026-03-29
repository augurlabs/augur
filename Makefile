#SPDX-License-Identifier: MIT

default:
	@ echo "Installation Commands:"
	@ echo "    install                         Installs Augur's full stack for production"
	@ echo "    wizard                          Install Augur and launch the graphical setup wizard"
	@ echo "    clean                           Removes potentially troublesome compiled files"
	@ echo "    rebuild                         Removes build/compiled files & binaries and reinstalls the project"
	@ echo
	@ echo "Development Commands:"
	@ echo "    db                              Initialize a fresh Docker database container (restarts it if it's still running)"
	@ echo "    dev                             Starts the full stack in the background"
	@ echo "    dev-start                       Runs the backend and frontend servers in the background"
	@ echo "    dev-stop                        Stops the backgrounded backend & frontend server commands"
	@ echo
	@ echo "Testing Commands:"
	@ echo "    test-data                       Start the testing dataset Docker database"
	@ echo "    test                            Runs all tests"
	@ echo "    test-api                        Run all API tests"
	@ echo
	@ echo "Documentation Commands:"
	@ echo "    docs                            Generates the documentation"
	@ echo "    docs-view                       Generates the documentation, then opens it for local viewing"

# @ echo "    test-application                Runs all application unit tests (including metrics)"
# @ echo "    test-workers                    Run all worker unit tests"


#
#  Installation
#
.PHONY: install
.PHONY: install-spdx install-spdx-sudo install-augur-sbom
.PHONY: clean rebuild
install: uv
	@ uv run ./scripts/install/install.sh dev

wizard:
	@ ./scripts/install/install.sh graphical

install-spdx:
	@ ./scripts/install/install-spdx.sh

install-spdx-sudo:
	@ ./scripts/install/install-spdx-sudo.sh

install-augur-sbom:
	@ ./scripts/install/nomos.sh

clean:
	@ scripts/control/clean.sh

rebuild: uv
	@ uv run scripts/control/rebuild.sh dev

#
#  Development
#
.PHONY: dev-start dev-stop dev monitor-frontend monitor-backend monitor frontend backend-stop backend-start backend-restart backend clean rebuild

dev-start:
	@ scripts/control/start_augur.sh
	@ scripts/control/start_frontend.sh

dev-stop:
	@ augur backend stop
	@ scripts/control/kill_frontend.sh

dev: dev-stop dev-start

db:
	@ - docker stop augur_database
	@ - docker rm augur_database
	@ docker run -p 5434:5432 --name augur_database augurlabs/augur:database


lint:
	@ pylint augur
lint-count:
	@ pylint augur | wc -l
lint-docs:
	@ pylint augur | grep docstring
lint-docs-missing:
	@ pylint augur | grep docstring | wc -l

lint-github-tasks-count:
	@ pylint augur | grep augur/tasks/github/ | wc -l

#
# Testing
#
.PHONY: test test-data test-application test-metric-routes test-python-versions

test-data:
	@ - docker stop augur_test_data
	@ - docker rm augur_test_data
	@ docker run -p 5434:5432 --name augur_test_data augurlabs/augur:test_data@sha256:71da12114bf28584a9a64ede2fac0cbc8dffc8e2f4a2c61231206e2f82201c2f

test:
	# @ pytest tests/test_tasks/test_github_tasks/
	@ python3 tests/start_server.py
	@ pytest tests/test_metrics/test_metrics_functionality/ tests/test_routes/test_api_functionality/ tests/test_tasks/ tests/test_application/ 
	@ python3 tests/stop_server.py

test-api:
	@ python3 tests/start_server.py
	@ pytest tests/test_metrics/test_metrics_functionality/ tests/test_routes/test_api_functionality/
	@ python3 tests/stop_server.py
	





#
# UV installation
#
.PHONY: uv
uv:
	@ command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; pip install --user uv; }

#
# Documentation
#
.PHONY: docs docs-view
docs: uv
	-rm -rf docs/build
	uv run --only-group docs make -C docs html

docs-view: docs
	@ bash -c 'open docs/build/html/index.html'


#
# Docker Shortcuts
# Do not use these unless you know what they mean.
.PHONY: compose-run compose-run-database
.PHONY: build-backend run-backend build-frontend run-frontend build-database run-database


compose-run:
	@ docker compose -f docker-compose.yml up --build

compose-run-database:
	@ echo "**************************************************************************"
	@ echo "Make sure there are no database credentials in docker_env.txt!"
	@ echo "**************************************************************************"
	@ echo
	@ docker compose -f docker-compose.yml -f database-compose.yml up --build

docker-build: docker-build-backend docker-build-frontend docker-build-database docker-build-rabbitmq

docker-build-backend:
	@ docker build -t augurlabs/augur:backend -f util/docker/backend/Dockerfile .

docker-build-frontend:
	@ docker build -t augurlabs/augur:frontend -f util/docker/frontend/Dockerfile .

docker-build-database:
	@ docker build -t augurlabs/augur:database -f util/docker/database/Dockerfile .

docker-build-rabbitmq:
	@ docker build -t augurlabs/augur:rabbitmq -f util/docker/rabbitmq/Dockerfile .

docker-run-backend:
	@ - docker stop augur_backend
	@ - docker rm augur_backend
	docker run -p 5000:5000 --name augur_backend --env-file docker_env.txt augurlabs/augur:backend

docker-run-frontend:
	@ - docker stop augur_frontend
	@ - docker rm augur_frontend
	docker run -p 8080:8080 --name augur_frontend augurlabs/augur:frontend

docker-run-database:
	@ - docker stop augur_database
	@ - docker rm augur_database
	docker run -p 5434:5432 --name augur_database augurlabs/augur:database

docker-run-rabbitmq:
	@ - docker stop augur_rabbitmq
	@ - docker rm augur_rabbitmq
	docker run -p 5434:5432 --name augur_rabbitmq augurlabs/augur:rabbitmq
