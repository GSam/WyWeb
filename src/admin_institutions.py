
        allow(["HEAD", "GET","POST"])
        redirect = "NO"
        options = " "
      
        selectedValue = ""
        
        if request:
            if request.params:
                if request.params['institution']:
                    selectedValue = request.params['institution']           
                    try:    
                        cursor = cherrypy.thread_data.db.cursor() 
                        query = ("SELECT institution_name from institution order by institution_name")
                        cursor.execute(query) 
                        for (institution) in cursor:
                            if institution[0] == selectedValue:
                                options = options + "<option selected>" + institution[0] + "</option>"
                            else:
                                options = options + "<option>" + institution[0] + "</option>"
                        cursor.close()
                    except mysql.connector.Error as err:
                        status = err
        displayInstitution = ""
        displayContact = ""
        displayWebsite = ""
        displayDescription = ""
        
        if selectedValue == "":
            try:       
                cursor = cherrypy.thread_data.db.cursor() 
                query = ("SELECT institution_name from institution order by institution_name")
                cursor.execute(query)
                selectedValue = ""
                for (institution) in cursor:
                        options = options + "<option>" + institution[0] + "</option>"
                        if selectedValue == "":
                            selectedValue = institution[0]
                            
                cursor.close()
            except mysql.connector.Error as err:
                status = err 
        try:       
            cursor = cherrypy.thread_data.db.cursor() 
            query = ("SELECT institution_name,description,contact,website from institution where institution_name = '" + selectedValue + "'")
            cursor.execute(query)
            for (institution_name,description,contact,website) in cursor:
                displayInstitution = institution_name
                displayDescription = description
                displayContact = contact
                displayWebsite = website
            selectedValue = ""
            cursor.close()
        except mysql.connector.Error as err:
            status = err                     
        
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("admin_institutions.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect,OPTION=options,
        INSTITUTION=displayInstitution,CONTACT=displayContact,WEBSITE=displayWebsite,DESCRIPTION=displayDescription)
    admin_institutions.exposed = True