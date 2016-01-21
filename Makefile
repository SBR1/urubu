GH-PAGES = ${HOME}/dev/urubu-gh-pages/

all: pull build push publish

build:
	python -m urubu build
	touch _build/.nojekyll

serve:
	python -m urubu serve

publish:
	git subtree push --prefix _build origin master

push:
	git push -u urubu master

pull:
	git pull -u urubu master

