function getFileData() {
    if ("files" in localStorage)
        return JSON.parse(localStorage["files"])
    return [
                {
                    text: 'Project 1',
                    state: {
                        opened: true
                    },
                    children: [
                        {
                            text: 'Hello World',
                            type: 'file',
                            data: "import whiley.lang.System\n\nmethod main(System.Console console):\n    console.out.println(\"Hello World\")",
                            state: {
                                selected: true
                            }
                        }
                    ]
                }
            ]
}

function saveFile() {
    var $files = $('#file-browser');

    function getRoot(data) {
        return $files.jstree('get_node', '#')
    };

    function toJS(data) {
        if (!data) 
            return {}

        var newChildren = []
        for (var i = 0; i < data.children.length; i++)
            newChildren[i] = toJS($files.jstree('get_node', data.children[i]))

        var newChildren_d = []
        for (var i = 0; i < data.children_d.length; i++)
            newChildren_d[i] = toJS($files.jstree('get_node', data.children[i]))

        data.children = newChildren;
        data.children_d = newChildren_d;
        delete data.parent
        delete data.parents

        return data;
    };
    
    localStorage["files"] = JSON.stringify(toJS(getRoot()));
}
