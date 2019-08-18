GH-PAGES = ${HOME}/dev/urubu-gh-pages/

all: download pull build commit push publish
sync: download pull status
publish: build push upload

commit:
	git commit -a

status:
	git status

setup:
	python3 -m venv env
	source env/bin/activate
	pip install -r requirements.txt

build:
	source env/bin/activate
	cd _python; ./generateimgmd.py; cd ..
	python -m urubu build
	touch _build/.nojekyll

serve:
	python -m urubu serve

download:
	cd .build; git pull origin master; cd ..

upload:
	cd .build; rm -R *; cp -R ../_build/* ./; git add .; git commit -a -m "Auto commit."; git push origin master; cd ..

push:
	git push

pull:
	git pull

