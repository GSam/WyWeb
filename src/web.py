__author__ = 'gregorygraham'


def safe(str1):
    return str(str1).replace("<","&lt;").replace(">","&gt;")
