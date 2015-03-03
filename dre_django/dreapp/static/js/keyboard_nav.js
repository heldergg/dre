/***********************************/
/* Dre suporting JavaScript        */
/*                                 */
/* Usage of this code is optional. */
/***********************************/

/* Keyboard navigation setup */

$(function() {
    $( "body" ).keydown( function( event ) {
        var prev_date = $("#prev_date").attr("href");
        if ( event.keyCode == 37 && $("#prev_date").length && event.shiftKey == true && event.ctrlKey == false ) {
            window.location.href = prev_date;
        };
        var next_date = $("#next_date").attr("href");
        if ( event.keyCode == 39 && $("#next_date").length && event.shiftKey == true && event.ctrlKey == false ) {
            window.location.href = next_date;
        };
        var next_page = $("#next_page").attr("href");
        if ( event.keyCode == 39 && $("#next_page").length && event.shiftKey == false && event.ctrlKey == false ) {
            window.location.href = next_page;
        };
        var prev_page = $("#prev_page").attr("href");
        if ( event.keyCode == 37 && $("#prev_page").length && event.shiftKey == false && event.ctrlKey == false ) {
            window.location.href = prev_page;
        };
        var last_page = $("#last_page").attr("href");
        if ( event.keyCode == 39 && $("#last_page").length && event.shiftKey == false && event.ctrlKey == true ) {
            window.location.href = last_page;
        };
        var first_page = $("#first_page").attr("href");
        if ( event.keyCode == 37 && $("#first_page").length && event.shiftKey == false && event.ctrlKey == true ) {
            window.location.href = first_page;
        };
    });
});
