/***********************************/
/* Tag suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/

$(function() {

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
            $(this).parent().next("div").slideDown("fast"); } 
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

    /* Ajaxy tag add */
});
