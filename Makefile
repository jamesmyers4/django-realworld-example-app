IMAGE := conduit-test

.PHONY: build test test-full

build:
	docker build -t $(IMAGE) .

# PR-gated run: unit + integration + auth/boundary tests. Excludes the
# optional performance-smoke marker (see conduit/apps/articles/tests/test_performance.py).
test: build
	docker run --rm $(IMAGE) pytest -m "not performance"

# Nightly full regression: everything, including the optional
# performance-smoke layer.
test-full: build
	docker run --rm $(IMAGE) pytest
