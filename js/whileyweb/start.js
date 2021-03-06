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
