myfiles = $(git ls-files)

default: build install
	echo "asd"

.PHONY: build
build: dist $(myfiles)
	-python -m pep517.build .


install:
	if [ 0=$$(python -c 'import networkxarithmetic') ]; then \
		pip uninstall graphtoarithmetic -y; \
		fi
	pip install dist/graphtoarithmetic-0.3-py3-none-any.whl --force-reinstall


test_newthing:
	python -m unittest newthing.test_newthing

test_datagraph_factory:
	#python -m unittest datagraph_factory.test_datagraph_factory.test_graph.test_factory_leaf
	python -m unittest datagraph_factory.test_datagraph_factory

clear:
	-rm -r dist/*
	-rm -r build
	-rm -r graphtoarithmetic.egg-info
