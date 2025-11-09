jQuery(document).ready(function ($) {
    $('.wp-block-gallery').each(function () {
        var gallerygroupid = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        var gallery = $(this);
        var isLinkedToMedia = 0;
        if ( gallery.find('a[href*="png"]').length || gallery.find('a[href*="jpg"]').length ) {
            console.log('Gallery Linked to media files');
            isLinkedToMedia = 1;
            gallery.attr('uk-lightbox', 'animation: scale');

        } else { 
            console.log('Gallery NOT linked to media');
        }
    });
});