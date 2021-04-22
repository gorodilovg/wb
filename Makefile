SHELL := /bin/bash
DMF := manage.py # DJANGO MANAGE FILE

fullrun:
	sudo service postgresql start
	make env

env:
	pipenv shell

run:
	python $(DMF)runserver

serve:
	cd frontend && npm run serve

migrate:
	python $(DMF)makemigrations
	python  $(DMF)migrate

createsuperuser:
	python $(DMF)createsuperuser

pytest:	
	pytest $(filter-out $@, $(MAKECMDGOALS))

coverage:
	coverage pytest backend $(filter-out $@, $(MAKECMDGOALS)) 
