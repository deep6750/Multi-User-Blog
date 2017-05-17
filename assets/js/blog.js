$(function () {
    $("body").on("input propertychange", ".floating-label-form-group", function (e) {
        $(this).toggleClass("floating-label-form-group-with-value", !!$(e.target).val());
    }).on("focus", ".floating-label-form-group", function () {
        $(this).addClass("floating-label-form-group-with-focus");
    }).on("blur", ".floating-label-form-group", function () {
        $(this).removeClass("floating-label-form-group-with-focus");
    });
});
jQuery(document).ready(function ($) {
    var MQL = 1170;


    if ($(window).width() > MQL) {
        var headerHeight = $('.navbar-custom').height();
        $(window).on('scroll', {
                previousTop: 0
            },
            function () {
                var currentTop = $(window).scrollTop();

                if (currentTop < this.previousTop) {

                    if (currentTop > 0 && $('.navbar-custom').hasClass('is-fixed')) {
                        $('.navbar-custom').addClass('is-visible');
                    } else {
                        $('.navbar-custom').removeClass('is-visible is-fixed');
                    }
                } else if (currentTop > this.previousTop) {

                    $('.navbar-custom').removeClass('is-visible');
                    if (currentTop > headerHeight && !$('.navbar-custom').hasClass('is-fixed')) $('.navbar-custom').addClass('is-fixed');
                }
                this.previousTop = currentTop;
            });
    }
    var errors = {
        "notLogged": "Require User To LogIn!",
        "notCmntOwner": "You Can Only Delete Your Comments!",
        "emptyCmnt": "Comment Can't Be Empty!",
        "notPostOwner": "You Can  Edit or Delete your Own Posts!",
        "ownPost": "You Can't Like Your Post"
    };

    function getQueryVariable(variable) {
        var query = window.location.search.substring(1);
        var vars = query.split("&");
        for (var i = 0; i < vars.length; i++) {
            var pair = vars[i].split("=");
            if (pair[0] == variable) {
                return pair[1];
            }
        }
        return (false);
    }



    if (getQueryVariable('error')) {
        var error = errors[getQueryVariable('error')];
        var $message = $("#message");
        $message.removeClass("hide");
        var content = document.createTextNode(error);
        $message.append(content);

    }
    $(function () {
        $(".i").click(function () {
            $(".i,.span").toggleClass("press", 1000);
        });
    });
});
