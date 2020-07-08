#########
Variables
#########

.. contents::

-----------------
What is variables
-----------------

Variables are used in creating questions and their
purpose is to have different values for different
students. Using variables a question can be used
multiple times with different values.

Each variable should have a unique name_.
The name is used in other parts of the question
to indicate the use of the variable.
Variables can have 4 different
types int_, float_, enum_, or expression_.

Each type has different attributes and the value
of that variables in generated based on those
attributes.

.. _name: `Variable names`_

--------------------
How to use variables
--------------------

In create/edit question pages you might find the
variables section. The variables are defined
per question.

+++++++++++++++++++++
Usage in the question
+++++++++++++++++++++

You can use the variables in other
sections of the question (e.g Statement, Choices).
To use the variables write `{{variable_name}}` with no
extra spaces in between. For example, if you have defined
a variable named `a`, you should write `{{a}}`. And it
will be replaced with the generated values of that
variable when someone views the question.

++++++++++++++++
Cascade property
++++++++++++++++

Variable attributes can be defined using previously
defined variables. For example, one might want to
create an integer variable named `a` between 1 and 100.
And then they want to create a float variable named `b`,
but the the range from `a` to `2*a`. This can be done by
setting the min attribute of variable `b` to `{{a}}` and the
max attribute of variable `b` to `2*{{a}}`. When rendering
the question the attributes of each variable will also be
rendered using the already defined variables. Therefor,
the order of variables is important. Each variable can
only use the variables defined before it.

--------------
Variable names
--------------

Technically variable names can be anything.
But it is recommended to use simple Python3-valid
variable names to avoid conflicts.

--------------
Variable types
--------------

+++
int
+++

This variable type generates a random integer
between min and max. If the given min or max
is not integer it will be casted to integer before
generating the random number.
For example, if you give min=3.5 and max=4.9,
after casting to integer we have min=3 and max=4.
Even though 3 is not between 3.5 and 4.9 but it
might be generated.

+++++
float
+++++

This variable type generate a random float
between min and max. You also need to define
how many digits after the decimal point you need
by the precision attribute.

++++
enum
++++

This variable type randomly chooses one of the given
values. The values are treated as strings.
You can still use previously defined variables, but
it will not evaluate mathematical expressions.

++++++++++
expression
++++++++++

This variable type generates a value based on an
expression.

--------------------------------
Available commands and operators
--------------------------------

All the Python3 operators and math library functions
are available to use. Due to security reasons,
no other function/method/class is accessible. If you
need another function to use please ask developers
to add it. Also feel free to add it yourself and
make a pull request in Github. Here are some
examples of what you can use.

+++++++++
operators
+++++++++

========= ============== ========
Operator  Definition     Example
========= ============== ========
\+        Add            ``3+2``
\-        Subtraction    ``3-2``
\*        Multiplication ``2*{{a}}``
\/        Division       ``3/2``
\%        Remainder      ``3%2``
\**       Power          ``3**2``
\//       Int Division   ``3//2``
========= ============== ========

`See all the operators <https://www.w3schools.com/python/python_operators.asp>`_

++++++++
commands
++++++++

========= ============== ========
Function  Definition     Example
========= ============== ========
sqrt      Square Root    sqrt(5)
round     Nearest Int    round(2.9)
sin       Sin Function   sin({{x}})
pi        Constant PI    2*pi
log       Natural log    log({{x}})
radians   Deg to Rad     radians(45)
e         Constant e     e**{{x}}
========= ============== ========

`See all the commands <https://docs.python.org/3/library/math.html>`_