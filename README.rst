==========================
Canvas Gamification
==========================

.. contents::
.. section-numbering::


Main Features
=============

Canvas Gamification is a platform where course instructors
can provide questions to their student in forms of practice,
assignments, quizzes, or exams.

Supported Types of Questions
----------------------------
* Multiple Choice
* Check Box
* Java Coding
* Parsons

Getting Started
===============

Dependencies
------------

* Python 3.7
    * *Required Packages* is listed in requirements.txt
* Docker
    * Required to run judge0 locally or deploying the website
    * `Installation <https://docs.docker.com/desktop/>`__
* Judge0 server
    * Provided in docker compose
* Mailing System
    * For production requires an SMTP mailing service. Provide the details in env files.
    * For local development the email will be printed in console.
* reCaptcha
    * For production, you need to obtain your reCaptcha key and provide it in env files.
    * `Details <https://www.google.com/recaptcha/about/>`__

Local Dev
---------

In local development you can set the environment variables in
env/gamification.dev.env. All the field are pre populated
so if you just want to run the website locally don't change it.

Go to canvas_gamification/settings.py and change

.. code-block:: bash

    DEBUG=True

Python
++++++

Ensure Python3 is installed, then upgrade/install pip

.. code-block:: bash

    python3 -m pip install pip --upgrade

Optionally you set virtual environment for python
install Pipenv

.. code-block:: bash

    python3 -m pip install pipenv

Next navigate to the project directory, once in the project directory create a virtual environment with Pipenv

.. code-block:: bash

    pipenv shell

To install all necessary dependencies

.. code-block:: bash

    pip install -r requirements.txt

Judge0
++++++

To be able to execute user's code you need to have judge0
up and running. docker-compose.dev.yml is ready to run judge0.
Environment variables in env/gamification.dev.env is set to use
this instance of judge0.

.. code-block:: bash

    sudo docker-compose -f docker-compose.dev.yml up -d

Run the Website
+++++++++++++++

Then apply the migrations

.. code-block:: bash

    python3 manage.py migrate

Now you can run the server by

.. code-block:: bash

    python3 manage.py runserver

To initialize sample questions you can use

.. code-block:: bash

    python3 manage.py populate-db --all

Admin User
++++++++++

To use the website you need an admin user.
Create a super use by

.. code-block:: bash

    python3 manage.py createsuperuser

You also need to give this user a teacher access to the website.

#. Open the website (Normally at localhost:8000)
#. Login with the super user you just created
#. Go to the admin section by clicking
   on the admin button at the top right of the screen
#. Go to the users section and click on your user
#. Scroll down and change the role from student to teacher
#. Save the user and open the website again

Tests
-----

.. code-block:: bash

    python3 manage.py test

Docker
------

For local development, it is recommended not to use docker
for the website but only for judge0 which is provided in
docker-compose.dev.yml

For production, copy env/gamification.sample.env to env/gamification.env.
Fill the variables in it and run the server by

.. code-block:: bash

    sudo docker-compose up -d

The server should be up and running on port 80

Documentation
=============

Documentation is located at "docs/" folder.

Generate the html file by running this code under docs/ directory

.. code-block:: bash

    make html

Authors
=======
Keyvan Khademi

- Email: keyvankhademi@gmail.com
- GitHub: `keyvankhademi <https://github.com/keyvankhademi>`__

Collaborators
=============
Opey Adeyemi

- Email: opeyadeyemi@gmail.com
- GitHub: `opeyem1a <https://github.com/opeyem1a>`__

Carson Ricca

- Email: carsonricca28@gmail.com
- GitHub: `carson-ricca <https://github.com/carson-ricca>`__

