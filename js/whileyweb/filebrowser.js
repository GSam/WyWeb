$(function() {
    $("#file-browser").jstree({
     core: {
            check_callback: true,
            data: getFileData()
        },
     plugins: ["contextmenu", "dnd", "types", "unique"],
     contextmenu: {
     items: function(node) {
                var tmp = $.jstree.defaults.contextmenu.items()
                delete tmp.create.action;
                tmp.create.submenu = {
                    create_folder: {
                        label: "Folder",
                        action: function(data) {
                            var inst = $.jstree.reference(data.reference),
                                obj = inst.get_node(data.reference);
                            inst.create_node(obj, {type: "default", text: "New folder"}, "last", function(new_node) {
                                setTimeout(function() {inst.edit(new_node);}, 0);
                            });
                        }
                    },
                    create_file: {
                        label: "File",
                        action: function(data) {
                            var inst = $.jstree.reference(data.reference),
                                obj = inst.get_node(data.reference);
                            inst.create_node(obj, {type: "file", text: "New File", data: ""}, "last",
                                function(new_node) {
                                    setTimeout(function() {inst.edit(new_node); }, 0);
                            })
                        }
                    }
                }
                if (this.get_type(node) == "file")
                    delete tmp.create;
                return tmp;
            }
        },
        types: {
            "default": {},
            "file": {
                max_children: 0,
                icon: "/images/wylogo_small.png"
            }
        }
    })
});
