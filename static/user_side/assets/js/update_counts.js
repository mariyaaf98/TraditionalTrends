function updateCounts() {
    $.ajax({
        url: "{% url 'ajax_get_counts' %}",
        method: "GET",
        success: function(data) {
            $('.pro-count.blue').each(function() {
                if ($(this).closest('a').attr('href').includes('wishlist')) {
                    $(this).text(data.wishlist_item_count);
                } else if ($(this).closest('a').attr('href').includes('cart')) {
                    $(this).text(data.cart_item_count);
                }
            });
        }
    });
}

// Call updateCounts() function on page load
$(document).ready(function() {
    updateCounts();
});
