 .PHONY: test
 test:
	rm -rf data
	poetry run pytest tests/

.PHONY: publish
publish:
	poetry build
	poetry publish