 .PHONY: test
 test:
	rm -rf data
	poetry run pytest tests/