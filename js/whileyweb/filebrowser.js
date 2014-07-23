$(function() {
    $("#file-browser").jstree({
        data : [
            {
                text: 'New Project',
                state: {
                    opened : true,
                    selected : true
                },
                children: [
                    'main.wy'
                ],
                li_attr: {},
                a_attr: {}
            }
        ]
    })
});
