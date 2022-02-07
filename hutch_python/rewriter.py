import functools
import inspect

import redbaron as rb


def rewriter(func):
    """Decorator to rewrite ``plan.run()`` into ``yield from plan()``."""
    source, lineno = inspect.getsourcelines(func)
    red = rb.RedBaron("".join(source))
    for decorator in list(red.find_all("DecoratorNode")):
        if decorator.name.value == "rewriter":
            decorator.replace("# Decorator placeholder")

    for node in red.find_all("AtomtrailersNode"):
        if not isinstance(node.parent, rb.YieldFromNode):
            if len(node.value) >= 2 and node[1].value == "run":
                trailer = node.copy()
                node.replace("yield from _")
                node.value = trailer
                trailer.value.pop(1)

    # TODO: better way to do this, I'm sure
    padding = "\n" * lineno
    rewritten_source = padding + red.dumps()

    code = compile(rewritten_source, inspect.getfile(func), "exec")
    exec(code, func.__globals__)
    new_function = func.__globals__[func.__name__]
    return functools.update_wrapper(new_function, func)
