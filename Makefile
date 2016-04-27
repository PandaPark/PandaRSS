venv:
	(\
	test -d venv || virtualenv venv;\
	venv/bin/pip install -U pip;\
	venv/bin/pip install -U -r requirements.txt;\
	venv/bin/pip install -e . ;\
	)

build:
	python setup.py bdist_wheel

register:
	python setup.py register

upload:
	python setup.py bdist_wheel upload

install:
	python setup.py install

clean:
	@rm -rf .Python MANIFEST build dist venv* *.egg-info *.egg
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete

.PHONY: build register upload install venv clean