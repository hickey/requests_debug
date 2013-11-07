test:
	pip install requests testfixtures pytest pytest-cov
	python setup.py develop
	py.test --cov requests_debug test.py

