/* This function is no longer needed */
/*$(document).on("ace-loaded", function autoindent() {
    editor.on("change", function(evt) {
        if (evt.data.action == "insertText" && evt.data.text == "\n") {
            var line = evt.data.range.end.row,
                prevLine = evt.data.range.start.row,
                doc = editor.getSession().getDocument(),
                prevLineText = doc.getLine(prevLine);
            if (prevLineText.charAt(prevLineText.length - 1) == ":")
                window.setTimeout(function() {editor.indent()}, 0);
        }
    })
});*/
/**
 * Compile a given snippet of Whiley code.
 */
function compile() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");

    // build parameters
    var $files = $('#file-browser');
    var main = getPath($files, $files.jstree('get_selected')[0]) + ".whiley";
    var request = { _main: main, _verify: verify.checked };
    if (main.indexOf('/') != -1) {
        main = main.split("/")[0];
    } else {
        main = getPath($files, $files.jstree('get_selected')[0]);
    }
    addFiles($files, "", "#", request, main);
    $.post(root_url + "/compile_all", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors(true);
            addMessage("success", "Compiled successfully.");
        } else if(response.result == "errors") {
            var errors = response.errors;
            showErrors(errors);
            addMessage("error", "Compilation failed: " + errors.length + " error" + (errors.length > 1 ? "s." : "."));
        } else if(response.result == "error") {
            clearErrors(true);
            addMessage("error", response.error);
        }
    });
    $("#spinner").show();
}

function exports(filename) {
    // build parameters
    var $files = $('#file-browser');
    var mainpath = getPath($files, $files.jstree('get_selected')[0]);
    var request = {_main: mainpath};
    if (mainpath.indexOf("/") != -1) {
        mainpath = mainpath.split("/")[0];
    }
    if(!filename){
    filename = mainpath;
    };
    addFiles($files, "", "#", request, mainpath);

    var clickEvent;
    clickEvent = document.createEvent("MouseEvent");
    clickEvent.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);

    var downloadButton = document.createElement('a');
    downloadButton.href = root_url + '/exports?' + $.param(request);
    downloadButton.download = filename + '.tar.gz';
    downloadButton.dispatchEvent(clickEvent);

    $("#spinner").show();
    $("#exportModal").modal("hide");
    $("#exportFilename").val("");
}

function addFiles($files, prefix, node, query, project) {
    var data = $files.jstree('get_node', node);
    if (data.type == "file")
        query[prefix + "/" + data.text + ".whiley"] = data.data;
    else if (data.type == "project" && project) {
        if (data.text == project) for (var i = 0; i < data.children.length; i++) {
            addFiles($files, data.text, data.children[i], query, project);
        }
    } else for (var i = 0; i < data.children.length; i++) {
        addFiles($files, prefix ? prefix + "/" + data.text : data.text, data.children[i], query, project);
    }
}
function getPath($files, node) {
    if (node == '#') return ""
    var data = $files.jstree('get_node', node);
    if (!data || !data.text || !data.text.length) return ""
    if (data.type == "project") return data.text
    return getPath($files, data.parent) + "/" + data.text;
}
/**
 * Display all the compilation errors.
 */
function showErrors(errors) {
    clearErrors();
    for(var i=0;i!=errors.length;++i) {
        var error = errors[i];
        markError(error);
    }
}

/**
 * Add an appropriate marker for a given JSON error object, as
 * returned from the server.
 */
function markError(error) {
    if(error.start !== "" && error.end !== "" && error.line !== "") {
        // Switch to appropriate file
        var filepath = error.filename.split("/").slice(2) // First 2 directories are gibberish
        var tree = $("#file-browser").jstree(true).get_json('#')
        for (var i = 0; i < filepath.length; i++) {
            var pathComponent = filepath[i].split(".")[0];
            if ("children" in tree) tree = tree.children;
            for (var j = 0; j < tree.length; j++) {
                if (tree[j].text == pathComponent) {
                    tree = tree[j]
                    break
                }
            }
        }

        window.setTimeout(function() {
            // Select it, and fill the text
            $("#file-browser").jstree(true).select_node(tree.id);

            // And mark the error
            editor.getSession().setAnnotations([{
                row: error.line - 1,
                column: error.start,
                text: error.text.replace("\\n", "\n"),
                type: "error"
            }]);
            var range = new ace.Range(error.line-1, error.start, error.line-1, error.end+1);
            editor.markers.push(editor.getSession().addMarker(range, "error-message", "error", false));
        }, 0);
    } else {
        addMessage("error", error.text);
    }
}

/**
 * Clear all the compilation errors.
 *
 * Clear all markers (including those in the gutter) from the editor.
 * This is to prevent markers from a previous compilation from hanging
 * around.
 */
function clearErrors() {
    editor.getSession().clearAnnotations();
    for (var i = 0; i < editor.markers.length; i++) {
        editor.getSession().removeMarker(editor.markers[i]);
    }
    editor.markers = [];
}

$(function() {
    $("#file-browser").jstree({
     core: {
            check_callback: true,
            data: getFileData()
        },
     plugins: ["contextmenu", "dnd", "types", "unique", "wholerow", "search"],
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
                            inst.create_node(obj, {type: "default", text: "NewFolder"}, "last", function(new_node) {
                                setTimeout(function() {inst.edit(new_node);}, 0);
                            });
                        }
                    },
                    create_file: {
                        label: "File",
                        action: function(data) {createNewFile(data);}
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
            },
            "project":{}
        }
    })
});

function createNewFile(data)
{
    var inst = $.jstree.reference(data.reference);
    var obj = inst.get_node(data.reference);
    inst.create_node(obj, {type: "file", text: "NewFile", data: ""}, "last",
        function(new_node) {
            setTimeout(function() {inst.edit(new_node); }, 0);
        }
    );
}
loggedStorage = undefined;

function getFileData() {
    if ("files" in localStorage && !isLoggedIn) {
        return JSON.parse(localStorage["files"])
    }

    if (isLoggedIn && loggedStorage != undefined) {
        return loggedStorage;
    }

    return serverFiles
}

function saveFile() {
    if (!isLoggedIn) {
        var $files = $('#file-browser');

        localStorage["files"] = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
    } else {
        var $files = $('#file-browser');
        loggedStorage = JSON.stringify($files.jstree(true).get_json('#', {'flat':true}));
    }
}
/**
 * Add a new message to the message list above the console.
 */
function addMessage(message_class, message_text, callback) {
    var message = $("<div></div>");
    message.text(message_text);
    message.addClass("message");
    message.addClass(message_class);
    message.appendTo("#messages");
    message.fadeIn(200).delay(2000).slideUp(200, function() {
        message.remove();
        if (callback !== undefined) {
            callback();
        }
    });
}

/**
 * Remove all messages from the message list above the console.
 */
function clearMessages() {
    $("#messages").children().remove();
}

var _selectedFile, _fileLoading = false;
var _newFile = false;

$(function() {
    $('#file-browser').on('changed.jstree', function(evt, data) {
		saveFile();
        if (data && data.node && "data" in data.node) {
            _fileLoading = true
            editor.setValue(data.node.data, 0);
            //console.log(data.node.type);
            if (data.node.type == "project" || data.node.type == "default")
            {
                jQuery("#toolbar a.enabled").hide();
                jQuery("#toolbar a.disabled").show();
				editor.setValue("", 0);
                editor.container.style.pointerEvents="none"
                editor.container.style.opacity=0.5
                editor.renderer.setStyle("disabled", true)
                editor.blur()
            }
            else if (data.node.type == "file")
            {
                jQuery("#toolbar a.disabled").hide();
                jQuery("#toolbar a.enabled").show();
                editor.container.style.pointerEvents="auto"
                editor.container.style.opacity=1.0
                editor.renderer.setStyle("disabled", false)
                editor.focus()
            }

            _newFile = true;
            _fileLoading = false
            _selectedFile = data.node
        }
    }).on('loaded.jstree', function() {
                jQuery("#toolbar a.disabled").hide();
                jQuery("#toolbar a.enabled").show();
            editor.container.style.pointerEvents="none"
            editor.container.style.opacity=0.5
            editor.renderer.setStyle("disabled", true)
            editor.blur()
        _selectedFile = $(this).jstree('get_node', $(this).jstree('get_selected')[0])
    }).on('delete_node.jstree', function(first, second){
        var $files = $('#file-browser');
        var request = { _project: second.node.text};
        alert(request._project);
        $.post(root_url + '/private_delete_project',  request, function() {});
    }).on('rename_node.jstree', function(first, second){
        var $files = $('#file-browser');
        console.log(first);
        console.log(second);
        var request = { _project: second.old, _new_name: second.text};
        alert(request._new_name);
        $.post(root_url + '/private_rename_project',  request, function() {});
    })
})

$(document).on('ace-loaded', function() {
    editor.on('change', function() {
        if (!_fileLoading) {
            _selectedFile.data = editor.getValue()
            saveFile()
            if (_newFile) {
                _newFile = false;
                editor.getSession().getUndoManager().reset()
            }
        }
    })
})

function addFile()
{

}

function addProject() {
    $('#file-browser').jstree("search",'UntitledProject');
    $('#file-browser').jstree('create_node', null, {text: 'UntitledProject'}, undefined, function(type) {
        $('#file-browser').jstree('set_type', type, 'project')
    })
}
function saveToServer() {
    _selectedFile.data = editor.getValue() // Fix, current file doesn't save correctly.

    var request = {};
    var $files = $('#file-browser');
    addFiles($files, "", "#", request);

    $.post(root_url + '/private_save',  request, function() {});
}
/**
 * Compile and run a given snippet of Whiley code.
 */
function run() {
    var console = document.getElementById("console");
    var verify = document.getElementById("verification");

    var $files = $('#file-browser');
    var main = getPath($files, $files.jstree('get_selected')[0]) + ".whiley";
    var request = { _main: main, _verify: verify.checked, _project: main.split('/')[0]};
    addFiles($files, "", "#", request, main.split("/")[0]);
    $.post(root_url + "/run_all", request, function(response) {
        clearMessages();
        console.value = "";
        $("#spinner").hide();
        var response = $.parseJSON(response);
        if(response.result == "success") {
            clearErrors(true);
            addMessage("success", "Compiled successfully. Running...");
            setTimeout(function() {console.value = response.output;}, 500);
        } else if(response.result == "errors") {
            var errors = response.errors;
            showErrors(errors);
            addMessage("error", "Compilation failed: " + errors.length + " error" + (errors.length > 1 ? "s." : "."));
        } else if(response.result == "error") {
            clearErrors(true);
            addMessage("error", response.error);
        }
    });
    $("#spinner").show();
}

// Global reference to the code editor.
var editor;

// Run this code when the page has loaded.
$(function() {
    editor.markers = [];
    /*ace.Range = require('ace/range').Range;
    // Enable the editor with Whiley syntax.
    editor = ace.edit("code");
    var WhileyMode = require("ace/mode/whiley").Mode;
    editor.getSession().setMode(new WhileyMode());
    editor.setTheme("ace/theme/eclipse");
    editor.setFontSize("10pt");
    editor.setBehavioursEnabled(false);
    editor.setHighlightActiveLine(false);
    editor.setShowFoldWidgets(false);
    editor.setShowPrintMargin(false);
    editor.getSession().setUseSoftTabs(true);
    editor.getSession().setTabSize(4);

    $("#code").resizable({
        resize: function() {
            editor.resize();
        },
        handles: "s",
        cursor: "default",
        minHeight: $("#code").height()
    });*/

    // If there is an error, display the error message for 5 seconds.
    if(error != "") {
        var error_message = $("<div></div>");
        error_message.text(error);
        error_message.addClass("error");
        error_message.addClass("message");
        error_message.prependTo("#content");
        error_message.show().delay(2000).fadeOut(500, function() {
            // If the user should be redirected to the main page (due to invalid ID for example), do so.
            if(redirect == "YES") {
                window.location.replace(root_url + "/");
            }
        });
    }

    // Override Ctrl-S for convenience
    editor.commands.addCommand({
        name: 'saveFile',
        bindKey: {
            win: 'Ctrl-S',
            mac: 'Command-S',
            sender: 'editor|cli'
        },
        exec: function(env, args, request) {
        }
    });

    // Prevent Ctrl-Z from undoing to the other files
    editor.commands.addCommand({
        name: 'File',
        bindKey: {
            win: 'Ctrl-Z',
            mac: 'Command-Z',
            sender: 'editor|cli'
        },
        exec: function(env, args, request) {
            if (_newFile) {
                _newFile = false;
                editor.getSession().getUndoManager().reset()
            }
            editor.undo()
        }
    });

    // Now activate all "behaviours" for the editor.
    $(document).trigger("ace-loaded");
});
