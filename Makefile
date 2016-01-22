GH-PAGES = ${HOME}/dev/urubu-gh-pages/

all: download pull build push publish

build:
	python -m urubu build
	touch _build/.nojekyll

serve:
	python -m urubu serve

download:
	cd .build; git pull origin master; cd ..

publish:
	cd .build; rm -R *; cp -R ../_build/* ./; git push origin master; cd ..

push:
	git push -u urubu master

pull:
	git pull -u urubu master

