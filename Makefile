build: python-packages links env/bin/srcml

.PHONY: links
links: env/bin/apply.py

env/bin/apply.py: env
	ln -s $$(realpath scripts/patch_apply/apply.py) env/bin

env/bin/srcml:
	if [ -z "$$(which srcml)" ]; then cd env; curl http://gehry.sdml.cs.kent.edu/lmcrs/v1.0.0/srcml_1.0.0-1_ubuntu20.04.tar.gz | tar -zxv ; else ln -s "$$(which srcml)" /env/bin/srcml; fi
	if [ -f "env/bin/srcml" ]; then mv env/bin/srcml env/bin/srcml-binary; echo '#!/bin/bash\nLD_LIBRARY_PATH=$(CURDIR)/env/lib exec srcml-binary $$*' >env/bin/srcml; chmod +x env/bin/srcml; fi;

.PHONY: python-packages
python-packages: env
	@if [ ! -d env/lib/python*/site-packages/diff_match_patch ]; then echo "Installing diff_match_patch"; . env/bin/activate; python3 -m pip install diff_match_patch; fi
	@if [ ! -d env/lib/python*/site-packages/Levenshtein ]; then echo "Installing Levenshtein"; . env/bin/activate; python3 -m pip install Levenshtein; fi
	@if [ ! -d env/lib/python*/site-packages/pygments ]; then echo "Installing diff_match_patch"; . env/bin/activate; python3 -m pip install pygments; fi
	@if [ ! -x env/bin/pytest ]; then echo "Installing pytest"; . env/bin/activate; python3 -m pip install pytest; fi
	@if [ ! -x env/bin/pytest-cov ]; then echo "Installing pytest-cov"; . env/bin/activate; python3 -m pip install pytest-cov; fi

env:
	python3 -m venv env
