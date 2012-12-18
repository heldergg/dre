/***********************************/
/* Tag suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/


/* Ajaxy tag delete */
function tagdelete_setup() {
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
    }; // End formtag_setup

$(function() {
    /* Hide and show the add tag form */
    $(".add_tag").addClass("hidden"); 
   
    var tag_form_visible = null;
    $(".tag_control").click( function() {
        if (tag_form_visible) {
            $(tag_form_visible).next("div").slideUp("fast");    
            $(tag_form_visible).find("img").attr("src", STATIC_URL + "img/add-tag.png");
            };
        if ( this != tag_form_visible ) {
            tag_form_visible = this; 
            $(this).find("img").attr("src", STATIC_URL + "img/remove-tag.png");
            $(this).next("div").slideDown("fast");
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

    /* Change pic when hovering */
    $(".remove_tag_img").hover(
        function () {
            $(this).attr("src", STATIC_URL + "img/remove-active.png");;
            }, 
        function () {
            $(this).attr("src", STATIC_URL + "img/remove-inactive.png");
            }
        );


    /* Ajaxy tag add */
    $(".add_tag form").submit(function () {
        var form_values = { 'name': $(this).find('input[name=name]').val(),
          'csrfmiddlewaretoken': $(this).find('input[name=csrfmiddlewaretoken]').val(), };
        var post_url = $(this).attr("action")
        var result_tag_list = $(this).parent().parent().find('.tags')
        var image = $(this).parent().parent().find('.tag_control').find('img')

        $(image).attr("src", STATIC_URL + "img/progress.gif");

        $.post( post_url, form_values, function (data) {
            $(image).attr("src", STATIC_URL + "img/remove-tag.png");
            if (data.success ) {
                var tag_html = "<span class='tag' style='color:#ffffff;background:#4060a2;'><span class='tag_remove'><a href='" + data.tag_remove_url + "'><img class='remove_tag_img' hight='16' width='16' src='/static/img/remove-inactive.png'></a></span>" + form_values["name"] + "</span>";
                $(result_tag_list).append(tag_html); 
                };
            $("#notification").html(data.message);
            $("#notification").fadeIn(200).delay(500).fadeOut(2000);
            tagdelete_setup()
            }, "json" );

        return false;
        });

    /* Initialize */
    tagdelete_setup()
    
});
