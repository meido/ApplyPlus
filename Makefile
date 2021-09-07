build: python-packages links

.PHONY: links
links: env/bin/apply.py

env/bin/apply.py: env
	ln -s $$(realpath scripts/patch_apply/apply.py) env/bin

.PHONY: python-packages
python-packages: env
	@if [ ! -d env/lib/python*/site-packages/diff_match_patch ]; then echo "Installing diff_match_patch"; . env/bin/activate; python3 -m pip install diff_match_patch; fi
	@if [ ! -d env/lib/python*/site-packages/Levenshtein ]; then echo "Installing Levenshtein"; . env/bin/activate; python3 -m pip install Levenshtein; fi
	@if [ ! -d env/lib/python*/site-packages/pygments ]; then echo "Installing diff_match_patch"; . env/bin/activate; python3 -m pip install pygments; fi
	@if [ ! -x env/bin/pytest ]; then echo "Installing pytest"; . env/bin/activate; python3 -m pip install pytest; fi

env:
	python3 -m venv env
