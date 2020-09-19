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
* Judge0 server
    * Provided in docker compose
* Mailing System
    * Requires an SMTP mailing service. Provide the details in settings.json

Local Dev
---------

Copy env/gamification.sample.env to env/gamification.env
and fill the missing fields.

Go to canvas_gamification/settings.py and change

.. code-block:: bash

    DEBUG=True

Ensure Python is installed, then upgrade/install pip

.. code-block:: bash

    python3 -m pip install pip --upgrade

Then install Pipenv

.. code-block:: bash

    python3 -m pip install pipenv

Next navigate to the project directory, once in the project directory create a virtual environment with Pipenv

.. code-block:: bash

    pipenv shell

Install Django

.. code-block:: bash

    pipenv install Django

To install all necessary dependencies

.. code-block:: bash

    pip install -r requirements.txt

Then apply the migrations

.. code-block:: bash

    ./manage.py migrate

or

.. code-block:: bash

    python3 manage.py migrate

Finally you can run the server by

.. code-block:: bash

    ./manage.py runserver

or

.. code-block:: bash

    python3 manage.py runserver

To initialize sample questions you can use

.. code-block:: bash

    ./manage.py populate-db --all

or

.. code-block:: bash

    python3 manage.py populate-db --all

Tests
-----

.. code-block:: bash

    ./manage.py test

Docker
------

A docker file is provided to run the website.
It is recommended to use the provided docker compose.

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

