
(function ($) {

    var init = function () {
        infiniteScroll();
        singleCharacters();
        backToTop();
        LikePost();
        modalPopup();
        commentsPostFocus();
    };

    $(document).ready(function () {
        init();
    });

    $(window).resize(function () {

    });

    var singleCharacters = function () {

        var blogHeight = $('.blog-single').height();

        $('.single-characters').each(function() {

            var charPosition = $(this).position();

            if(charPosition.top > blogHeight - 350) {
                $(this).hide();
            }

        });

    }

    var modalPopup = function () {

        if($("#scopely-popup").length != 0) {

            if (sessionStorage.getItem('openedPopup') !== 'true') {
                UIkit.modal('#scopely-popup').show();
                sessionStorage.setItem('openedPopup','true');
            }
        }
    }

    var commentsPostFocus = function () {

        $('.comment-form input[type="text"], .comment-form input[type="url"], .comment-form input[type="email"], .comment-form textarea').each(function(){
            $(this).change(function(){
                if($(this).val()!=""){
                    $(this).css({'background-color': 'white'})
                } else {
                    $(this).css({'background-color': 'transparent'})
                }
            }); 
        }); 

        
    }

    
    var backToTop = function () {

        $(window).scroll(function(){ 
            if ($(this).scrollTop() > 600) { 
                $('.back-to-top').show(); 
            } else { 
                $('.back-to-top').hide(); 
            } 
        }); 
        $('.back-to-top').click(function(){ 
            $("html, body").animate({ scrollTop: 0 }, 600); 
            return false; 
        }); 
    }

    var LikePost = function () {

        $('.scopely-likes').on('click', function() {
            var link = $(this);
            if (link.hasClass('active')) return false;
        
            var id = $(this).attr('id'),
                postfix = link.find('.scopely-likes-postfix').text();
        
            $.ajax({
              type: 'POST',
              url: scopely_likes.ajaxurl,
              data: {
                action: 'scopely-likes', 
                likes_id: id, 
                postfix: postfix, 
              },
              xhrFields: { 
                withCredentials: true, 
              },
              success: function(data) {
                link.html(data).addClass('active').attr('title','You already like this');
              },
            });
        
            return false;
          });
        
          if ($('body.ajax-scopely-likes').length) {
            $('.scopely-likes').each(function() {
              var id = $(this).attr('id');
              $(this).load(scopely_likes.ajaxurl, {
                action: 'scopely-likes', 
                post_id: id,
              });
            });
          }

    }

    var infiniteScroll = function () {
        
        $('.show-more').click(function(){

            var button = $( this ),
                data = {
                'action': 'infinite_scroll',
                'query': infinite_scroll_params.posts, // that's how we get params from wp_localize_script() function
                'page' : infinite_scroll_params.current_page,
                'max_page' : infinite_scroll_params.max_page,
            };
    
                $.ajax({
                    url : infinite_scroll_params.ajaxurl, // AJAX handler
                    data : data,
                    type : 'POST',
                    beforeSend : function ( xhr ) {
                        button.addClass('loading');
                    },
                    success : function( data ){
    
                        if( data ) {

                            button.removeClass('loading');
                            $('#blog-posts').append(data); // insert new posts
    
                            infinite_scroll_params.current_page++;
    
                            if ( infinite_scroll_params.current_page == infinite_scroll_params.max_page ) {
                                button.remove(); // if last page, remove the button
                            }
                        }
                    }
                });
    
    
        });

    }

})(jQuery);
