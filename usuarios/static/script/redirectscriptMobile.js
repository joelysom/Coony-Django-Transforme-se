// Redirect script
    function redirectByWidth() {
    if (window.innerWidth > 768) {
        // Desktop
        if (!window.location.href.includes("index.html")) {
        window.location.href = "index.html";
        }
    } else {
        // Mobile
        if (!window.location.href.includes("mobile.html")) {
        window.location.href = "mobile.html";
        }
    }
    }

    // Roda no carregamento
    redirectByWidth();

    // Roda sempre que a tela é redimensionada
    window.addEventListener("resize", redirectByWidth);
