__author__ = 'gregorygraham'


def safe(str1):
    """
    Replaces angle brackets in order to prevent browser injection attacks.

    >>> safe("Long long ago in a galaxy far far away")
    'Long long ago in a galaxy far far away'
    >>> safe("<em>Long long ago</em> in a <strong>galaxy</strong> far far away")
    '&lt;em&gt;Long long ago&lt;/em&gt; in a &lt;strong&gt;galaxy&lt;/strong&gt; far far away'
    """
    return str(str1).replace("<","&lt;").replace(">","&gt;")
