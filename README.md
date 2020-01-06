# listing-grader

This is a Django application that accepts a submission via API  and uses django-background-tasks to do seller listing
analysis then submit to a webflow account. Currently the listings are specific to Amazon only.

### Deployment
Currently, deployment is manual. This means logging into the server and manually pulling code updates and restarting services 

1. SSH into listing grader server
2. cd /listing_grader_project/django/
3. wget https://github.com/Zentail-Growth-Team/listing-grader/archive/master.zip
4. unzip master.zip
5. cp -r listing-grader-master/* listing_grader_project/
6. sudo service apache restart
7. sudo service listing-grader restart

### Notes on the above
There are 2 parts to this project. The main django application and the listing-grader service, which processes the submissions.
The listing-grader service is just running a django manage command "process_tasks".
For running any other additional django manage commands you need to make sure and activate the virtualenv:
1. cd /listing_grader_project/django/listing_grader_project/
2. source ../venv/bin/activate

For installing any new python requirements added to the requirements.txt file you must do that first as well then run:
1. pip install -r requirements.txt