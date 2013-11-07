test:
	pip install requests testfixtures pytest pytest-cov
	py.test --cov requests_debug test.py

