/*
 * Mobile Menu
 */

/* config */
var visible = false;

/* Resize actions */

function resize_action() {
    var win = $( window );
    var width = win.width();

    if (width <= 800) {
        $("#mobile_menu").show();
        $("#main_menu").hide();
        $("#menu_back").hide();
        visible = false;
    } else {
        $("#mobile_menu").hide();
        $("#main_menu").show();
    };
};

function setup_resolution_change() {
    $( window ).resize(function() {
        resize_action();
    });
};

/* Menu functions */

function setup_mobile_menu() {
    $("#toggle_menu").click( function() {
        if (visible) {
            $("#main_menu").hide();
            $("#menu_back").hide();
            visible = false;
        } else {
            $("#main_menu").show();
            $("#menu_back").show();
            visible = true;
        };
    });

    $("#menu_back").click( function() {
        $("#main_menu").hide();
        $("#menu_back").hide();
        visible = false;
    });

    $("#main_menu").mouseleave( function() {
        if ($(window).width() <= 800) {
            setTimeout(function(){
                var wide = $(window).width() > 800;
                if (!( $("#main_menu:hover").length ) && !wide) {
                    $("#main_menu").hide();
                    $("#menu_back").hide();
                    visible = false;
                };
            }, 2000);
        };
    });
};

/* Initialization */

$(function() {
    setup_mobile_menu();
    setup_resolution_change();
});


