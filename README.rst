==========================
Canvas Gamification
==========================

.. contents::
.. section-numbering::


Main Features
=============

Canvas Gamification is a platform where course instructors
can provide questions to their student in forms of practice,
assignments, quizzes, or exams. This project now serves as the backend to the newer Canvas Gamification UI project. This project interacts with the Angular project through APIs, and the functionality of the website has been maintained in the migration to Angular.

Supported Question Types
----------------------------
* Multiple Choice
* Check Box
* Java Coding
* Parsons

Getting Started
===============

Cloning the Project
-------------------

If you are using windows please run this command
before you clone the project. It will prevent the line endings
to change from LF ro CRLF.

.. code-block:: bash

    git config --global core.autocrlf input

Dependencies
------------

* Python 3.7
    * *Required Packages* is listed in requirements.txt
* Docker
    * Required to run judge0 locally or deploying the website.
    * `Installation <https://docs.docker.com/desktop/>`__
* Judge0 server
    * Provided in docker compose
* Mailing System
    * For production requires an SMTP mailing service. Provide the details in env files.
    * For local development the email will be printed in console.
* reCaptcha
    * For production, you need to obtain your reCaptcha key and provide it in env files.
    * `Details <https://www.google.com/recaptcha/about/>`__
    * For local development, recaptcha will be automatically validated.

Local Development
-----------------

In local development you can set the environment variables in
``env/gamification.dev.env``. All the fields are pre-populated
so if you just want to run the website no changes are required.

PyCharm Settings
++++++++++++++++

If you are developing in PyCharm (our recommendation), it is important to ensure that `Django Support` is enabled.

#. Ensure that you have installed `PyCharm Professional Edition`, you can get a free license as a student. `https://www.jetbrains.com/community/education/#students <https://www.jetbrains.com/community/education/#students/>`__.
#. `PyCharm -> Preferences -> Language & Frameworks -> Django`.
#. Ensure that `Enable Django Support` is checked.

Windows
+++++++

If on Windows it is important to note that you must have a C++ compiler installed locally in order to be able to install some of the dependencies (i.e. ``python-Levenshtein``).

#. Navigate to `https://visualstudio.microsoft.com/downloads/ <https://visualstudio.microsoft.com/downloads/>`__.
#. Download the `Visual Studio 2019 Community Edition`
#. After downloading `Visual Studio 2019`, scroll to the `All Downloads` section at the bottom of the page.
#. Select `Tools for Visual Studio 2019`. Scroll to the bottom of the dropdown and download `Build Tools for Visual Studio 2019`.
#. After downloading the build tools, launch `Visual Studio 2019`.
#. An option to install `C++ Build Tools` should now be available within `Visual Studio 2019`. Install the build tools.
#. After installing the build tools, launch a new terminal and continue with the setup.


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
up and running. ``docker-compose.dev.yml`` prepares and runs judge0.
The environment variables in ``env/gamification.dev.env`` are set to use
this instance of judge0.

.. code-block:: bash

    sudo docker-compose -f docker-compose.dev.yml up -d

Run the Website
+++++++++++++++

Apply the migrations

.. code-block:: bash

    python3 manage.py migrate

Now you can run the server by

.. code-block:: bash

    python3 manage.py runserver

To initialize sample questions you can use

.. code-block:: bash

    python3 manage.py populate-db --all

To access the api endpoints navigate to ``localhost:8000/api``.    

Admin User
++++++++++

To use the website you need an admin user.
Create a super user by

.. code-block:: bash

    python3 manage.py createsuperuser

You also need to give this user a teacher access to the website.

#. Open the website's admin portal (normally at ``localhost:8000/admin``).
#. Login with the super user you just created.
#. Go to the users section and click on your user.
#. Scroll down and change the role from student to teacher.
#. Save the user.

Tests
-----

.. code-block:: bash

    python3 manage.py test

Docker
------

For local development, it is recommended not to use docker
for the website but only for judge0 which is provided in
``docker-compose.dev.yml``.

For production, copy ``env/gamification.sample.env`` to ``env/gamification.env``.
Fill in the required variables and run the server with

.. code-block:: bash

    sudo docker-compose up -d

The server should be up and running on port 80

Documentation
=============

Code Documentation
------------------

Documentation is located in the ``docs/`` directory.

Generate the html file by running this code in the ``docs/`` directory.

.. code-block:: bash

    make html

API Documentation
-----------------

API Documentation is auto-generated from code
and is accessible at ``/api/docs``.

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

