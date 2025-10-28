.PHONY: test
test:
	python -m pytest -q

tools/rngd/rngd: tools/rngd/rngd.cpp
	@mkdir -p tools/rngd
	c++ -O2 -std=c++17 $< -o $@

run-rngd: tools/rngd/rngd
	./tools/rngd/rngd
