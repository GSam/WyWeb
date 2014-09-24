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

    // Now activate all "behaviours" for the editor.
    $(document).trigger("ace-loaded");
});
