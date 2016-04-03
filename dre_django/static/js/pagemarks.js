/* Bookmarks within a page */

var markers = [];

function place_flag( mark_value ) {
    $("body").append('<div class="flag" style="top:' + mark_value + 'px;"><div class="circle"><img src="/static/img/mark.svg" width="10px"></div></div>')
};

function cmp(a, b) {
    return a-b;
};

$(function() {
    if ((document.documentElement.scrollHeight - document.documentElement.clientHeight) < 1200)
        /* No page marks for small pages */
        return;
    $("#pagemarks").show();

    $("#mark").click( function() {
        if (markers.indexOf(window.scrollY) != -1)
            /* No duplicate markers */
            return;
        if (window.scrollY == 0 || window.scrollY == (document.documentElement.scrollHeight - document.documentElement.clientHeight))
            /* No markers at the begining or end of the page */
            return;
        markers.push(window.scrollY);
        markers.sort(cmp);
        place_flag(window.scrollY);
    });

    $("body").on('click', 'div.flag' , function(){
        var mark = parseInt($(this).css("top"), 10);
        var index = markers.indexOf(mark);
        markers.splice(index, 1);
        $(this).remove();
    });

    $("#go_up").click( function() {
        var cur_pos = window.scrollY;
        var target_pos = 0;
        for (var i = 0; i < markers.length; i++) {
            if (markers[i] < cur_pos)
                target_pos = markers[i];
        };
        window.scrollTo(0, target_pos);
    });

    $("#go_down").click( function() {
        var cur_pos = window.scrollY;
        var target_pos = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        for (var i = 0; i < markers.length; i++) {
            if (markers[i] > cur_pos) {
                target_pos = markers[i];
                break;
            };
        };
        window.scrollTo(0, target_pos);
    });
});
