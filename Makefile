# Minimal makefile for Sphinx documentation

# You can set these SPHINX related variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build
CODEDIR       = src/pyracf

# Make options for the python code

build:
	python -m build

upload:
	python -m twine upload --skip-existing --repository pypi dist/*

# SPHINX help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# create autodoc stubs for new modules
apidoc:
	sphinx-apidoc -o "$(SOURCEDIR)/source" "$(CODEDIR)" 

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

