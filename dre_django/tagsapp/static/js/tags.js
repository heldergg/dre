/***********************************/
/* Tag suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/


function tagdelete_setup() {
    /* Ajaxy tag delete */
    $(".tag_remove").click(function (e) { 
        e.preventDefault(); 
        var delete_url = $(this).find("a").attr("href");
        tag_remove = $(this).parent()

        // Delete the tag
        $.getJSON( delete_url, function(data, a, b) {
            $("#notification").html(data.message);
            $("#notification").fadeIn(200).delay(500).fadeOut(2000);
            if (data.success) {
                tag_remove.fadeOut(1000); 
                };
            });
        });

    /* Change pic when hovering */
    $(".remove_tag_img").hover(
        function () {
            $(this).attr("src", STATIC_URL + "img/remove-active.png");;
            }, 
        function () {
            $(this).attr("src", STATIC_URL + "img/remove-inactive.png");
            }
        );
    }; // End formtag_setup

function form_setup() {
    /* Hide and show the add tag form */
    $(".add_tag").addClass("hidden"); 
   
    var tag_form_visible = null;
    $(".tag_control").click( function() {
        if (tag_form_visible) {
            $(tag_form_visible).parent().next("div").slideUp("fast");    
            $(tag_form_visible).find("img").attr("src", STATIC_URL + "img/add-tag.png");
            };
        if ( this != tag_form_visible ) {
            tag_form_visible = this; 
            $(this).find("img").attr("src", STATIC_URL + "img/remove-tag.png");
            $(this).parent().next("div").slideDown("fast");
            }
        else {
            tag_form_visible = null;
            };
        }); 

    /* Auto complete */
    $(".tag_name_input").autocomplete({
        source: "/tag/suggest/",
        minLength: 2,
        });
    }; // form_setup

function ajax_add_setup() {
    /* Ajaxy tag add */
    $(".add_tag form").submit(function () {
        var form_values = { 'name': $(this).find('input[name=name]').val(),
          'csrfmiddlewaretoken': $(this).find('input[name=csrfmiddlewaretoken]').val(), };
        var post_url = $(this).attr("action")
        var result_tag_list = $(this).parent().parent().find('.tag_list')
        var image = $(this).parent().parent().find('.tag_control').find('img')

        $(image).attr("src", STATIC_URL + "img/progress.gif");

        $.post( post_url, form_values, function (data) {
            $(image).attr("src", STATIC_URL + "img/remove-tag.png");
            if (data.success ) {
                var tag_html = "<span class='tag' style='color:#ffffff;background:#4060a2;'><span class='tag_remove'><a href='" + data.tag_remove_url + "'><img class='remove_tag_img' hight='16' width='16' src='/static/img/remove-inactive.png'></a></span><span class='tag_name'>" + form_values["name"] + "</span></span>";
                $(result_tag_list).append(tag_html); 
                };
            $("#notification").html(data.message);
            $("#notification").fadeIn(200).delay(500).fadeOut(2000);
            tagdelete_setup();
            draggables_setup();
            }, "json" );

        return false;
        });
    }; // ajax_add_setup

function draggables_setup() {
    /* Draggables */
    $(".tag").draggable({
            helper: "clone",
            zIndex: 2700
            });

    $(".result_item").droppable({
        over: function( event, ui ) { $(this).addClass("highlight"); },
        out: function( event, ui ) { $(this).removeClass("highlight"); },
        deactivate: function( event, ui ) { $(this).removeClass("highlight"); },

        drop: function( event, ui ) {
            /* Get the form url and parameters */
            var form = $(this).find(".add_tag").find("form");
            var post_url = form.attr("action")
            var result_tag_list = $(this).find('.tag_list')
            var image = $(this).find('.tag_control').find('img')
            var old_image = image.attr("src")
            var name = ui.draggable.find(".tag_name").html()

            $(image).attr("src", STATIC_URL + "img/progress.gif");

            var form_values = { 
                "name": name,
                "csrfmiddlewaretoken": form.find("input[name=csrfmiddlewaretoken]").val(), };
            
            /* Add the tag to the target */
            $.post( post_url, form_values, function (data) {
                $(image).attr("src", STATIC_URL + "img/remove-tag.png");
                if (data.success ) {
                var tag_html = "<span class='tag' style='color:#ffffff;background:#4060a2;'><span class='tag_remove'><a href='" + data.tag_remove_url + "'><img class='remove_tag_img' hight='16' width='16' src='/static/img/remove-inactive.png'></a></span><span class='tag_name'>" + form_values["name"] + "</span></span>";
                    $(result_tag_list).append(tag_html); 
                    };
                $("#notification").html(data.message);
                $("#notification").fadeIn(200).delay(500).fadeOut(2000);
                tagdelete_setup();
                draggables_setup();
                $(image).attr("src",old_image);
                }, "json" );
            
            return false; 
            }, 
        });

    }; // draggables_setup



$(function() {
    if (is_owner) {
        form_setup();
        tagdelete_setup();
        ajax_add_setup();
        draggables_setup();
        };
});
