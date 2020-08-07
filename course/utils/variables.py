import math
from random import Random

MATH_NAMES = {
    k: v for k, v in math.__dict__.items() if not k.startswith("__")
}

STR_NAMES = {
    k: v for k, v in str.__dict__.items() if not k.startswith("__")
}

ALLOWED_NAMES = {
    **MATH_NAMES,
    **STR_NAMES,
    'len': len,
}


def evaluate(expression):
    code = compile(expression, "<string>", "eval")

    for name in code.co_names:
        if name not in ALLOWED_NAMES:
            raise NameError(f"The use of '{name}' is not allowed")

    return eval(code, {"__builtins__": {}}, ALLOWED_NAMES)


def render_text(text, variables):
    text = str(text)
    for variable, value in variables.items():
        text = text.replace("{{" + variable + "}}", str(value))
    return text


def _generate_variable(attrs, variables, random):

    vtype = attrs.get('type', None)
    vmin = evaluate(render_text(attrs.get('min', 0), variables))
    vmax = evaluate(render_text(attrs.get('max', 1), variables))
    precision = evaluate(render_text(attrs.get('precision'), variables))
    exp = render_text(attrs.get('expression', ''), variables)
    values = [render_text(x, variables) for x in attrs.get('values', [])]

    if vtype == 'int':
        variables[attrs['name']] = random.randrange(int(vmin), int(vmax) + 1)
    if vtype == 'float':
        value = random.uniform(vmin, vmax + 1)
        precision = 10 ** precision
        value = math.floor(value * precision) / precision
        variables[attrs['name']] = value
    if vtype == 'enum':
        p = random.randrange(0, len(values))
        variables[attrs['name']] = values[p]
    if vtype == 'expression':
        variables[attrs['name']] = evaluate(exp)


def generate_variables(variable_schema, seed):
    random = Random()
    random.seed(seed)
    variables = {}
    errors = []

    if type(variable_schema) != list:
        return {}, ["Invalid schema type.", ]

    for attrs in variable_schema:
        if 'name' not in attrs:
            errors.append("Name was not defined for a variable!")
            continue

        name = attrs['name']

        if name in variables.keys():
            errors.append("Duplicate variable name detected!")
            continue

        try:
            _generate_variable(attrs, variables, random)
        except NameError as e:
            errors.append("{}: {}".format(name, e.args))
        except Exception as e:
            errors.append("{}: {}".format(name, e.args))

    return variables, errors
