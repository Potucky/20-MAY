.PHONY: test smoke unit negative

PYTEST = python -m pytest

test:
	$(PYTEST)

smoke:
	$(PYTEST) -m smoke

unit:
	$(PYTEST) -m unit

negative:
	$(PYTEST) -m negative
