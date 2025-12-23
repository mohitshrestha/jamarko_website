// product.js
// Modern, modular product gallery, lightbox, variant handling, and cart

document.addEventListener("DOMContentLoaded", () => {
    const mainImage = document.getElementById("mainImage");
    const carousel = document.getElementById("thumbnailCarousel");
    const leftArrow = document.querySelector(".carousel-arrow.left");
    const rightArrow = document.querySelector(".carousel-arrow.right");
    const variantSelect = document.getElementById("variantSelect");
    const addToCartBtn = document.getElementById("addToCartBtn");
    const skuElement = document.getElementById("productSKU");

    // -----------------------------
    // THUMBNAIL SWAP
    // -----------------------------
    const initThumbnailSwap = () => {
        document.querySelectorAll("[data-thumb]").forEach(thumb => {
            thumb.addEventListener("click", () => {
                if (mainImage) mainImage.src = thumb.src;
                highlightSelectedThumbnail(thumb);
            });
        });
    };

    const highlightSelectedThumbnail = (thumb) => {
        document.querySelectorAll("[data-thumb]").forEach(t => t.classList.remove("selected"));
        thumb.classList.add("selected");
    };

    // -----------------------------
    // LIGHTBOX / ZOOM
    // -----------------------------
    const createLightbox = (src) => {
        const overlay = document.createElement("div");
        overlay.className = "lightbox-overlay";

        const img = document.createElement("img");
        img.src = src;
        img.className = "lightbox-image";

        overlay.appendChild(img);
        document.body.appendChild(overlay);

        const closeLightbox = () => overlay.remove();

        overlay.addEventListener("click", closeLightbox);
        document.addEventListener("keydown", function escListener(e) {
            if (e.key === "Escape") {
                closeLightbox();
                document.removeEventListener("keydown", escListener);
            }
        });
    };

    const initLightbox = () => {
        mainImage?.addEventListener("click", () => createLightbox(mainImage.src));
    };

    // -----------------------------
    // VARIANT SELECT
    // -----------------------------
    const initVariantSelect = () => {
        variantSelect?.addEventListener("change", (e) => {
            const selectedOption = e.target.selectedOptions[0];
            if (!selectedOption) return;

            const sku = selectedOption.dataset.sku;
            const price = selectedOption.dataset.price;
            const slug = selectedOption.value;

            // Update SKU display
            skuElement && (skuElement.textContent = `SKU: ${sku}`);

            // Update Add to Cart dataset
            addToCartBtn && Object.assign(addToCartBtn.dataset, { sku, price });

            // Navigate to child variant page if different
            const currentSlug = window.location.pathname.split("/").pop().replace(".qmd", "");
            if (slug && slug !== currentSlug) {
                window.location.href = slug + ".html";
            }
        });
    };

    // -----------------------------
    // CART HANDLING
    // -----------------------------
    const initAddToCart = () => {
        addToCartBtn?.addEventListener("click", () => {
            const { sku, price } = addToCartBtn.dataset;
            if (!sku || !price) {
                alert("Please select a valid variant first.");
                return;
            }

            const cart = JSON.parse(localStorage.getItem("cart") || "[]");
            const existingItem = cart.find(item => item.sku === sku);

            if (existingItem) {
                existingItem.qty += 1;
            } else {
                cart.push({ sku, price, qty: 1 });
            }

            localStorage.setItem("cart", JSON.stringify(cart));
            alert("Added to cart"); // Can be replaced with better visual feedback
        });
    };

    // -----------------------------
    // CAROUSEL
    // -----------------------------
    const initCarousel = () => {
        if (!carousel || !leftArrow || !rightArrow) return;

        const scrollAmount = carousel.firstElementChild?.clientWidth || 100;

        leftArrow.addEventListener("click", () => {
            carousel.scrollBy({ left: -scrollAmount, behavior: "smooth" });
        });

        rightArrow.addEventListener("click", () => {
            carousel.scrollBy({ left: scrollAmount, behavior: "smooth" });
        });
    };

    // -----------------------------
    // INITIALIZATION
    // -----------------------------
    const init = () => {
        initThumbnailSwap();
        initLightbox();
        initVariantSelect();
        initAddToCart();
        initCarousel();
    };

    init();
});
