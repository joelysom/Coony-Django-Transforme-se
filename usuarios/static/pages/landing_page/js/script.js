document.addEventListener('DOMContentLoaded', function () {
    /* ========= CARROSSEL DE CARDS ========= */
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(function (carousel) {
        const container = carousel.querySelector('.carousel__items');
        const prevButton = carousel.querySelector(
            '.carousel__button--prev'
        );
        const nextButton = carousel.querySelector(
            '.carousel__button--next'
        );
        const firstCard = container.querySelector('.card');

        function getScrollAmount() {
            if (!firstCard) return 0;
            const gap = parseFloat(
                window.getComputedStyle(container).columnGap || 0
            );
            const cardWidth = firstCard.offsetWidth;
            return (cardWidth + gap) * 2; // desloca por 2 cards
        }

        prevButton.addEventListener('click', function () {
            container.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
        });

        nextButton.addEventListener('click', function () {
            container.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
        });
    });

    /* ========= MENU MOBILE ========= */
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    const nav = document.getElementById('main-nav'); 

    if (mobileBtn && nav) {
        mobileBtn.addEventListener('click', function () {
            nav.classList.toggle('is-open');
            mobileBtn.classList.toggle('is-open');
        });
    }
});