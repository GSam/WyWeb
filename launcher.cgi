#!/usr/bin/env python

import sys

# Set up the path.
sys.path.insert(0, "lib")
sys.path.insert(0, "src")

import config
import cherrypy
import main
import admin
import auth

cherrypy_config = {
    "global": {
        "log.screen": None
    },
    "/": {
    	"tools.sessions.on": True,
    	'tools.auth.on': True,
        "request.show_tracebacks": False,
        "request.show_mismatched_params": False,
        "log.error_file": config.ERROR_LOG
    }
}
#cherrypy.quickstart(main.Main(), config=cherrypy_config)
cherrypy.tree.mount(main.Main(), config=cherrypy_config)
cherrypy.tree.mount(auth.AuthController(), '/auth', config=cherrypy_config)

cherrypy.engine.start()
cherrypy.engine.block()

