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

Copy setting.sample.json to settings.json
and fill the missing fields.

Then apply the migrations

.. code-block:: bash

    ./manage.py migrate

Finally you can run the server by

.. code-block:: bash

    ./manage.py runserver

To initialize sample questions you can use

.. code-block:: bash

    ./manage.py populate-db --all

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

