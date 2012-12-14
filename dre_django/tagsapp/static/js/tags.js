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
            $(this).parent().next("div").slideDown("fast");
            } else {
            tag_form_visible = null;
            };
        }); 

    /* Auto complete */
    $(".tag_name_input").autocomplete({
        source: "/tag/suggest/",
        minLength: 2,
        });

    /* Ajaxy tag delete */

    /* Ajaxy tag add */
});
