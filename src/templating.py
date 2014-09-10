"""
A facade around Mako templates that evaluates lazily so that 
the context can be conveniently tested.
"""

try:
    from mako.template import Template
    from mako.lookup import TemplateLookup

    lookup = TemplateLookup(directories=['html', '../html'])
except ImportError:
    class _mock(object):
        def get_template(self, *args):
            return self
        def render(self, *args, **kwargs):
            return ""
    lookup = _mock()

class AnnotatedString(str):
    """A string that can be annotated with properties.

    >>> string = AnnotatedString("Hello")
    >>> string.FOO = 'bar'
    >>> string.FOO
    'bar'
    """

def render(__file, **__context):
    """
    This function's returns a string annotated by the values from
    the keyword arguments.
    
    >>> render("test.txt", FOO="BAR").FOO
    'BAR'
    >>> render("test.txt", FOO="BAR")
    'Hello BAR!\\n'
    """
    ret = AnnotatedString(lookup.get_template(__file).render(**__context))

    for prop, value in __context.items():
        setattr(ret, prop, value)

    return ret
