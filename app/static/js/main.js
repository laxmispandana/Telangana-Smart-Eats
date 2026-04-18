const grid = document.getElementById("restaurant-grid");
const searchInput = document.getElementById("search-input");
const navSearchInput = document.getElementById("nav-search");
const foodFilter = document.getElementById("food-filter");
const ratingFilter = document.getElementById("rating-filter");
const healthyFilter = document.getElementById("healthy-filter");
const radiusFilter = document.getElementById("radius-filter");
const locationBtn = document.getElementById("location-btn");
const locationStatus = document.getElementById("location-status");
const razorpayPayBtn = document.getElementById("razorpay-pay-btn");
const paymentStatus = document.getElementById("payment-status");
const upiCreateBtn = document.getElementById("upi-create-btn");
const upiConfirmBtn = document.getElementById("upi-confirm-btn");
const upiIdInput = document.getElementById("upi-id-input");
const upiModal = document.getElementById("upi-modal");
const upiQrImage = document.getElementById("upi-qr-image");
const upiAppLinks = document.getElementById("upi-app-links");
const upiTransactionId = document.getElementById("upi-transaction-id");
const upiModalStatus = document.getElementById("upi-modal-status");
const cartBadge = document.getElementById("cart-badge");
const floatingCartCount = document.getElementById("floating-cart-count");
const miniCart = document.getElementById("mini-cart");
const miniCartBody = document.getElementById("mini-cart-body");
const miniCartClose = document.getElementById("mini-cart-close");
const toastStack = document.getElementById("toast-stack");
const trackingShell = document.getElementById("tracking-shell");
const orderTimeline = document.getElementById("order-timeline");
const orderStatusLabel = document.getElementById("order-status-label");
const orderPaymentStatus = document.getElementById("order-payment-status");

let map;
let markerLayer;
let userCoords = null;
let lastRestaurants = [];
let activeCity = locationStatus?.dataset.fallbackCity || "Hyderabad";
let selectedPaymentMethod = "UPI";
let upiSession = null;
let cartState = { count: Number(cartBadge?.textContent || 0), total: 0, items: [] };

function syncSearchInputs(source, target) {
    if (!source || !target) return;
    if (target.value !== source.value) target.value = source.value;
}

function showToast(title, body = "", level = "info") {
    if (!toastStack) return;
    const node = document.createElement("article");
    node.className = `toast toast-${level}`;
    node.innerHTML = `<strong>${title}</strong><p>${body}</p>`;
    toastStack.appendChild(node);
    window.setTimeout(() => node.remove(), 4200);
}

function skeletonMarkup(count = 6) {
    return Array.from({ length: count })
        .map(() => '<article class="skeleton-card"></article>')
        .join("");
}

function renderRestaurantCard(restaurant) {
    const distanceLabel = restaurant.distance !== null ? `${restaurant.distance} km away` : restaurant.city;
    const tags = [
        restaurant.category === "diet" || restaurant.category === "veg" ? '<span class="tag">Healthy 🥗</span>' : "",
        restaurant.popular ? '<span class="tag">Popular 🔥</span>' : "",
        restaurant.distance !== null ? `<span class="tag">${restaurant.distance} km</span>` : "",
    ].join("");

    return `
        <article class="restaurant-card">
            <img loading="lazy" src="${restaurant.image_url}" alt="${restaurant.name}">
            <div class="restaurant-card-overlay">
                <div class="restaurant-topline">
                    <div>
                        <h3>${restaurant.name}</h3>
                        <p>${restaurant.area}, ${restaurant.city}</p>
                    </div>
                    <strong>⭐ ${restaurant.rating}</strong>
                </div>
                <div class="nutrition-row">${tags}</div>
                <p>${restaurant.cuisine}</p>
                <div class="menu-footer">
                    <span>${distanceLabel} • ${restaurant.delivery_time} mins</span>
                    <a href="/restaurants/${restaurant.id}" class="btn btn-mini">View Menu</a>
                </div>
            </div>
        </article>
    `;
}

async function loadRestaurants() {
    if (!grid) return;

    grid.innerHTML = skeletonMarkup();
    const params = new URLSearchParams({
        search: searchInput?.value || navSearchInput?.value || "",
        food_type: foodFilter?.value || "",
        rating: ratingFilter?.value || "0",
        healthy: healthyFilter?.checked ? "true" : "false",
        radius: radiusFilter?.value || "10",
        city: activeCity || "Hyderabad",
    });

    if (userCoords) {
        params.set("lat", userCoords.latitude);
        params.set("lng", userCoords.longitude);
    }

    try {
        const response = await fetch(`/restaurants/data?${params.toString()}`);
        const restaurants = await response.json();
        lastRestaurants = restaurants;
        grid.innerHTML = restaurants.length
            ? restaurants.map(renderRestaurantCard).join("")
            : "<p>No nearby restaurants matched these filters. Try a wider radius or reset the category filters.</p>";
        updateMap();
    } catch (_error) {
        grid.innerHTML = "<p>Unable to load restaurants right now.</p>";
    }
}

function initMap() {
    const mapNode = document.getElementById("map");
    if (!mapNode || map || typeof L === "undefined") return;

    map = L.map("map").setView([17.385, 78.4867], 7);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    markerLayer = L.layerGroup().addTo(map);
}

function updateMap() {
    if (!map || !markerLayer) return;

    markerLayer.clearLayers();
    lastRestaurants.forEach((restaurant) => {
        if (restaurant.lat == null || restaurant.lng == null) return;
        L.marker([restaurant.lat, restaurant.lng])
            .bindPopup(`<strong>${restaurant.name}</strong><br>${restaurant.area}, ${restaurant.city}`)
            .addTo(markerLayer);
    });

    if (userCoords) {
        L.circleMarker([userCoords.latitude, userCoords.longitude], {
            radius: 8,
            color: "#fc8019",
            fillColor: "#fc8019",
            fillOpacity: 1,
        }).bindPopup("You are here").addTo(markerLayer);
        map.setView([userCoords.latitude, userCoords.longitude], 11);
    }
}

async function resolveLocationContext(coords = null) {
    const params = new URLSearchParams({ fallback_city: activeCity || "Hyderabad" });
    if (coords) {
        params.set("lat", coords.latitude);
        params.set("lng", coords.longitude);
    }

    const response = await fetch(`/location/context?${params.toString()}`);
    if (!response.ok) throw new Error("Unable to resolve location.");
    return response.json();
}

async function requestLocation() {
    if (!navigator.geolocation) {
        userCoords = null;
        if (locationStatus) {
            locationStatus.textContent = `Geolocation is not supported in this browser. Showing top restaurants in ${activeCity}.`;
        }
        loadRestaurants();
        return;
    }

    if (locationStatus) locationStatus.textContent = "Finding restaurants near your live location...";

    navigator.geolocation.getCurrentPosition(
        async ({ coords }) => {
            try {
                const context = await resolveLocationContext(coords);
                userCoords = coords;
                activeCity = context.city || activeCity;
                if (locationStatus) {
                    locationStatus.textContent = `Showing restaurants within ${radiusFilter?.value || 10} km of your live location near ${activeCity}.`;
                }
            } catch (_error) {
                userCoords = coords;
                if (locationStatus) {
                    locationStatus.textContent = `Showing restaurants within ${radiusFilter?.value || 10} km of your live location.`;
                }
            }
            loadRestaurants();
        },
        async () => {
            userCoords = null;
            try {
                const context = await resolveLocationContext();
                activeCity = context.city || activeCity;
            } catch (_error) {
                activeCity = activeCity || "Hyderabad";
            }
            if (locationStatus) {
                locationStatus.textContent = `Location access denied. Showing the best FoodSprint picks in ${activeCity}.`;
            }
            loadRestaurants();
        },
        { enableHighAccuracy: true, timeout: 8000 }
    );
}

function renderMiniCart(items = []) {
    if (!miniCartBody) return;
    if (!items.length) {
        miniCartBody.innerHTML = '<p class="mini-cart-empty">Your cart is empty.</p>';
        return;
    }
    miniCartBody.innerHTML = items
        .slice(0, 3)
        .map(
            (item) => `
            <div class="mini-cart-item">
                <img src="${item.image || "/static/img/food-placeholder.svg"}" alt="${item.name}">
                <div>
                    <strong>${item.name}</strong>
                    <p>${item.quantity} x Rs. ${item.price || ""}</p>
                </div>
            </div>
        `
        )
        .join("");
}

function updateCartBadge(count) {
    if (cartBadge) cartBadge.textContent = count;
    if (floatingCartCount) floatingCartCount.textContent = count;
}

function showMiniCart() {
    if (!miniCart) return;
    miniCart.classList.add("mini-cart-open");
}

function hideMiniCart() {
    miniCart?.classList.remove("mini-cart-open");
}

function openUpiModal() {
    if (upiModal) upiModal.hidden = false;
}

function closeUpiModal() {
    if (upiModal) upiModal.hidden = true;
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return response.json();
}

async function addItemToCart(itemId) {
    try {
        const result = await postJson("/cart/add", { item_id: itemId, quantity: 1 });
        if (result.ok) {
            updateCartBadge(result.count);
            cartState.count = result.count;
            cartState.total = result.total;
            const itemName =
                document.querySelector(`[data-item-id="${itemId}"]`)?.closest(".menu-list-item")?.querySelector("h3")?.textContent ||
                "Item";
            const itemImage =
                document.querySelector(`[data-item-id="${itemId}"]`)?.closest(".menu-list-item")?.querySelector("img")?.src || "";
            const existing = cartState.items.find((item) => String(item.id) === String(itemId));
            if (existing) {
                existing.quantity += 1;
            } else {
                cartState.items.unshift({ id: itemId, name: itemName, image: itemImage, quantity: 1, price: "" });
            }
            renderMiniCart(cartState.items);
            showMiniCart();
            updateQuantityDisplay(itemId, Number(document.querySelector(`.qty-display[data-item-id="${itemId}"]`)?.textContent || 0) + 1);
        }
    } catch (_error) {
        showToast("Cart issue", "We could not update your cart right now.", "danger");
    }
}

async function updateItemQuantity(itemId, delta) {
    const display = document.querySelector(`.qty-display[data-item-id="${itemId}"]`);
    const current = Number(display?.textContent || 0);
    const quantity = Math.max(0, current + delta);
    try {
        const result = await postJson("/cart/update", { item_id: itemId, quantity });
        if (result.ok) {
            updateCartBadge(result.count);
            updateQuantityDisplay(itemId, quantity);
            showMiniCart();
        }
    } catch (_error) {
        showToast("Cart issue", "We could not update the quantity.", "danger");
    }
}

function updateQuantityDisplay(itemId, quantity) {
    document.querySelectorAll(`.qty-display[data-item-id="${itemId}"]`).forEach((node) => {
        node.textContent = quantity;
    });
}

async function triggerRazorpayCheckout() {
    if (!window.foodSprintCheckout?.enabled) return;
    razorpayPayBtn.disabled = true;
    razorpayPayBtn.textContent = "Preparing payment...";
    if (paymentStatus) paymentStatus.textContent = "Setting up secure Razorpay test checkout...";

    try {
        const orderResponse = await fetch(window.foodSprintCheckout.createOrderUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ preferred_method: selectedPaymentMethod }),
        });
        const orderData = await orderResponse.json();
        if (!orderData.ok) throw new Error(orderData.message || "Unable to create order.");

        const options = {
            key: orderData.key,
            amount: orderData.amount,
            currency: orderData.currency,
            name: orderData.name,
            description: orderData.description,
            order_id: orderData.razorpay_order_id,
            prefill: orderData.prefill,
            theme: { color: "#fc8019" },
            handler: async function (response) {
                if (paymentStatus) paymentStatus.textContent = "Verifying payment...";
                const verifyResponse = await fetch(window.foodSprintCheckout.verifyUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        internal_order_id: orderData.internal_order_id,
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_signature: response.razorpay_signature,
                    }),
                });
                const verifyData = await verifyResponse.json();
                if (verifyData.ok) {
                    window.location.href = verifyData.redirect_url;
                } else {
                    window.location.href = `${window.foodSprintCheckout.failureUrl}?order_id=${orderData.internal_order_id}`;
                }
            },
            modal: {
                ondismiss: function () {
                    window.location.href = `${window.foodSprintCheckout.failureUrl}?order_id=${orderData.internal_order_id}`;
                },
            },
        };

        const razorpay = new window.Razorpay(options);
        razorpay.open();
    } catch (error) {
        if (paymentStatus) {
            paymentStatus.textContent = error.message || "We could not start Razorpay checkout. Please try direct UPI.";
        }
        razorpayPayBtn.disabled = false;
        razorpayPayBtn.textContent = "Pay with Razorpay";
    }
}

async function createUpiRequest() {
    if (!window.foodSprintCheckout?.manualUpiEnabled) return;
    upiCreateBtn.disabled = true;
    if (upiModalStatus) upiModalStatus.textContent = "Generating your UPI request...";

    try {
        const response = await postJson(window.foodSprintCheckout.createUpiUrl, {
            upi_id: upiIdInput?.value?.trim() || "",
        });
        if (!response.ok) throw new Error(response.message || "Unable to generate UPI request.");

        upiSession = response;
        if (upiQrImage) upiQrImage.src = response.qr_code;
        if (upiAppLinks) {
            upiAppLinks.innerHTML = Object.entries(response.intent_links)
                .map(([key, href]) => `<a class="btn btn-mini" href="${href}">${key.toUpperCase()}</a>`)
                .join("");
        }
        if (upiModalStatus) upiModalStatus.textContent = "Complete payment in your app, then enter the UTR below.";
        openUpiModal();
    } catch (error) {
        if (upiModalStatus) upiModalStatus.textContent = error.message || "Unable to generate UPI request.";
        showToast("UPI unavailable", error.message || "Unable to generate UPI request.", "danger");
    } finally {
        upiCreateBtn.disabled = false;
    }
}

async function confirmUpiPayment() {
    if (!upiSession) return;
    upiConfirmBtn.disabled = true;
    if (upiModalStatus) upiModalStatus.textContent = "Submitting UPI payment proof...";
    try {
        const response = await postJson(window.foodSprintCheckout.confirmUpiUrl, {
            order_id: upiSession.order_id,
            transaction_id: upiTransactionId?.value?.trim() || "",
            upi_id: upiIdInput?.value?.trim() || "",
        });
        if (!response.ok) throw new Error(response.message || "Unable to submit proof.");
        window.location.href = response.redirect_url;
    } catch (error) {
        if (upiModalStatus) upiModalStatus.textContent = error.message || "Unable to submit UPI proof.";
    } finally {
        upiConfirmBtn.disabled = false;
    }
}

function renderTimeline(timeline = []) {
    if (!orderTimeline) return;
    orderTimeline.innerHTML = timeline
        .map(
            (event) => `
            <div class="timeline-step timeline-step-active">
                <span class="timeline-dot"></span>
                <div>
                    <strong>${event.status}</strong>
                    <p>${event.note || "Order updated"}</p>
                    <small>${event.created_at}</small>
                </div>
            </div>
        `
        )
        .join("");
}

function setupRealtime() {
    if (typeof io === "undefined" || !window.foodSprintRealtime?.hasUser && !window.foodSprintRealtime?.hasAdmin) return;
    const socket = io();
    if (trackingShell?.dataset.orderId) {
        socket.emit("join_order_room", { order_id: trackingShell.dataset.orderId });
    }
    socket.on("toast", (payload) => showToast(payload.title, payload.body, payload.level));
    socket.on("cart_updated", (payload) => {
        updateCartBadge(payload.count);
    });
    socket.on("order_status_updated", (payload) => {
        if (trackingShell && String(payload.order_id) === trackingShell.dataset.orderId) {
            if (orderStatusLabel) orderStatusLabel.textContent = payload.status;
            if (orderPaymentStatus) orderPaymentStatus.textContent = payload.payment_status.replaceAll("_", " ");
            renderTimeline(payload.timeline);
        }
        if (payload.message) {
            showToast("Order update", payload.message, "success");
        }
    });
}

function setupStickyHeader() {
    const header = document.querySelector(".site-header");
    if (!header) return;
    const toggle = () => header.classList.toggle("site-header-scrolled", window.scrollY > 8);
    toggle();
    window.addEventListener("scroll", toggle);
}

function setupCategoryChips() {
    document.querySelectorAll(".category-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".category-chip").forEach((node) => node.classList.remove("active"));
            chip.classList.add("active");
            if (foodFilter) foodFilter.value = chip.dataset.category || "";
            loadRestaurants();
        });
    });
}

function setupPaymentPills() {
    document.querySelectorAll(".payment-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".payment-pill").forEach((node) => node.classList.remove("active"));
            pill.classList.add("active");
            selectedPaymentMethod = pill.dataset.preferredMethod || "UPI";
        });
    });
}

[searchInput, foodFilter, ratingFilter, healthyFilter, radiusFilter].forEach((node) => {
    node?.addEventListener("input", loadRestaurants);
    node?.addEventListener("change", loadRestaurants);
});

searchInput?.addEventListener("input", () => syncSearchInputs(searchInput, navSearchInput));
navSearchInput?.addEventListener("input", () => {
    syncSearchInputs(navSearchInput, searchInput);
    if (grid) loadRestaurants();
});

radiusFilter?.addEventListener("change", () => {
    if (userCoords && locationStatus) {
        locationStatus.textContent = `Showing restaurants within ${radiusFilter.value} km of your live location near ${activeCity}.`;
    }
});

locationBtn?.addEventListener("click", requestLocation);
razorpayPayBtn?.addEventListener("click", triggerRazorpayCheckout);
upiCreateBtn?.addEventListener("click", createUpiRequest);
upiConfirmBtn?.addEventListener("click", confirmUpiPayment);
miniCartClose?.addEventListener("click", hideMiniCart);
document.querySelectorAll("[data-close-upi-modal]").forEach((node) => node.addEventListener("click", closeUpiModal));

document.addEventListener("click", (event) => {
    const addButton = event.target.closest(".js-add-to-cart");
    if (addButton) {
        addItemToCart(addButton.dataset.itemId);
        return;
    }

    const qtyButton = event.target.closest(".js-update-cart");
    if (qtyButton) {
        updateItemQuantity(qtyButton.dataset.itemId, Number(qtyButton.dataset.delta || 0));
    }
});

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    if (grid) loadRestaurants();
    setupStickyHeader();
    setupCategoryChips();
    setupPaymentPills();
    setupRealtime();
});
