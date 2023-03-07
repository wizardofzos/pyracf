build:
	python -m build

upload:
	python -m twine upload --skip-existing --repository pypi dist/*