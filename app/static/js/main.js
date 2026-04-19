const navSearch = document.getElementById("nav-search");
const restaurantList = document.getElementById("restaurantList");
const siteHeader = document.querySelector(".site-header");
const cartBadge = document.getElementById("cart-badge");
const miniCart = document.getElementById("miniCart");
const miniCartBody = document.getElementById("miniCartBody");
const miniCartTotal = document.getElementById("miniCartTotal");
const miniCartClose = document.getElementById("miniCartClose");

const nearbyState = {
    initialized: false,
    map: null,
    clusterLayer: null,
    userMarker: null,
    currentLat: null,
    currentLon: null,
    currentFoodType: "",
};

function filterRestaurantCards(query) {
    if (!restaurantList) return;
    const normalized = (query || "").trim().toLowerCase();
    restaurantList.querySelectorAll(".restaurant-card").forEach((card) => {
        const haystack = [
            card.dataset.name || "",
            card.dataset.city || "",
            card.dataset.cuisine || "",
        ].join(" ");
        card.style.display = haystack.includes(normalized) ? "" : "none";
    });
}

function updateHeaderState() {
    if (!siteHeader) return;
    siteHeader.classList.toggle("site-header-scrolled", window.scrollY > 10);
}

function cartCurrency(value) {
    return `Rs. ${Math.round(Number(value) || 0)}`;
}

function openMiniCart() {
    if (miniCart) miniCart.classList.add("mini-cart-open");
}

function closeMiniCart() {
    if (miniCart) miniCart.classList.remove("mini-cart-open");
}

function renderMiniCart(cart) {
    if (!miniCartBody || !miniCartTotal) return;

    miniCartTotal.textContent = cartCurrency(cart.total);
    if (!cart.entries || cart.entries.length === 0) {
        miniCartBody.innerHTML = '<p class="mini-cart-empty">Your cart is empty.</p>';
        return;
    }

    miniCartBody.innerHTML = cart.entries
        .map(
            (entry) => `
                <div class="mini-cart-item">
                    <img src="${entry.image_url}" alt="${entry.name}">
                    <div>
                        <strong>${entry.name}</strong>
                        <p>${entry.quantity} x ${cartCurrency(entry.price)}</p>
                    </div>
                </div>
            `
        )
        .join("");
}

function updateCartBadge(count) {
    if (cartBadge) {
        cartBadge.textContent = count;
    }
    const floatingCartCount = document.querySelector(".floating-cart-button strong");
    if (floatingCartCount) {
        floatingCartCount.textContent = count;
    }
}

function syncItemQuantity(itemId, quantity) {
    document.querySelectorAll(`[data-cart-controls][data-item-id="${itemId}"]`).forEach((control) => {
        const addButton = control.querySelector("[data-cart-add]");
        const qtyWrapper = control.querySelector("[data-qty-wrapper]");
        const qtyDisplay = control.querySelector("[data-cart-qty]");

        if (qtyDisplay) qtyDisplay.textContent = quantity;
        if (addButton) addButton.hidden = quantity > 0;
        if (qtyWrapper) qtyWrapper.hidden = quantity === 0;
    });
}

function updateCartPageSummary(cart) {
    const cartPageCount = document.getElementById("cartPageCount");
    const cartPageTotal = document.getElementById("cartPageTotal");
    if (cartPageCount) cartPageCount.textContent = cart.count;
    if (cartPageTotal) cartPageTotal.textContent = cartCurrency(cart.total);
}

function updateCartItemCards(cart) {
    const cartLayout = document.querySelector(".cart-layout");
    if (!cartLayout) return;

    const entryMap = new Map(cart.entries.map((entry) => [String(entry.item_id), entry]));
    document.querySelectorAll("[data-cart-item-card]").forEach((card) => {
        const entry = entryMap.get(String(card.dataset.itemId));
        if (!entry) {
            card.remove();
            return;
        }
        const subtotal = card.querySelector("[data-cart-subtotal]");
        if (subtotal) subtotal.textContent = cartCurrency(entry.subtotal);
    });

    if (cart.entries.length === 0) {
        cartLayout.outerHTML = `
            <div class="empty-state">
                <h3>Your cart is empty</h3>
                <p>Start with a restaurant near you and build your order in a few taps.</p>
                <a href="/" class="btn btn-primary">Browse restaurants</a>
            </div>
        `;
    }
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

async function refreshCartState() {
    if (!cartBadge) return;
    const response = await fetch("/cart?format=json");
    if (!response.ok) return;
    const cart = await response.json();
    updateCartBadge(cart.count);
    updateCartPageSummary(cart);
    updateCartItemCards(cart);
    renderMiniCart(cart);

    const quantities = new Map(cart.entries.map((entry) => [String(entry.item_id), entry.quantity]));
    document.querySelectorAll("[data-cart-controls]").forEach((control) => {
        syncItemQuantity(control.dataset.itemId, quantities.get(String(control.dataset.itemId)) || 0);
    });
}

async function changeCartQuantity(itemId, delta, absoluteQuantity = null) {
    const control = document.querySelector(`[data-cart-controls][data-item-id="${itemId}"]`);
    const currentQty = Number(control?.querySelector("[data-cart-qty]")?.textContent || 0);
    const nextQty = absoluteQuantity !== null ? absoluteQuantity : Math.max(currentQty + delta, 0);
    const endpoint = delta > 0 && currentQty === 0 && absoluteQuantity === null ? "/cart/add" : "/cart/update";
    const payload = endpoint === "/cart/add"
        ? { item_id: Number(itemId), quantity: 1 }
        : { item_id: Number(itemId), quantity: nextQty };

    const cart = await postJson(endpoint, payload);
    updateCartBadge(cart.count);
    updateCartPageSummary(cart);
    updateCartItemCards(cart);
    renderMiniCart(cart);
    syncItemQuantity(itemId, nextQty);
    openMiniCart();
}

function installCartHandlers() {
    document.addEventListener("click", async (event) => {
        const addButton = event.target.closest("[data-cart-add]");
        const plusButton = event.target.closest("[data-cart-plus]");
        const minusButton = event.target.closest("[data-cart-minus]");
        if (!addButton && !plusButton && !minusButton) return;

        event.preventDefault();
        try {
            if (addButton) {
                await changeCartQuantity(addButton.dataset.itemId, 1);
            } else if (plusButton) {
                await changeCartQuantity(plusButton.dataset.itemId, 1);
            } else if (minusButton) {
                await changeCartQuantity(minusButton.dataset.itemId, -1);
            }
        } catch (error) {
            console.error("Cart update failed", error);
        }
    });

    miniCartClose?.addEventListener("click", closeMiniCart);
}

function formatPlaceSubtitle(place) {
    const bits = [];
    if (place.address) bits.push(place.address);
    if (place.cuisine) bits.push(place.cuisine);
    if (place.type) bits.push(place.type.replaceAll("_", " "));
    return bits.join(" • ");
}

function buildNearbyCard(place, highlightFirst = false) {
    const imageMarkup = place.image_url
        ? `<img loading="lazy" src="${place.image_url}" alt="${place.name}">`
        : '<div class="restaurant-card-map-fallback">OpenStreetMap place</div>';
    const actionMarkup = place.url
        ? `<a href="${place.url}" class="btn btn-mini">View Menu</a>`
        : `<span class="tag">Map place</span>`;
    const ratingMarkup = place.rating ? `<strong>⭐ ${place.rating}</strong>` : `<strong>${place.distance_km.toFixed(1)} km</strong>`;

    return `
        <article class="restaurant-card static-card ${highlightFirst ? "restaurant-card-nearest" : ""}">
            ${imageMarkup}
            <div class="restaurant-card-overlay">
                <div class="restaurant-topline">
                    <div>
                        <h3>${place.name}</h3>
                        <p>${place.area ? `${place.area}, ${place.city}` : place.city || "Nearby area"}</p>
                    </div>
                    ${ratingMarkup}
                </div>
                <div class="nutrition-row">
                    <span class="tag">${(place.source || "osm").toUpperCase()}</span>
                    ${place.delivery_time ? `<span class="tag">${place.delivery_time} mins</span>` : ""}
                    <span class="tag">${place.distance_km.toFixed(1)} km</span>
                </div>
                <p>${formatPlaceSubtitle(place) || "Nearby restaurant found from OpenStreetMap."}</p>
                <div class="menu-footer">
                    <span>${highlightFirst ? "Nearest right now" : "Nearby option"}</span>
                    ${actionMarkup}
                </div>
            </div>
        </article>
    `;
}

function renderNearbyRestaurants(payload) {
    const list = document.getElementById("nearbyRestaurantsList");
    const cards = document.getElementById("nearbyRestaurantCards");
    const locationStatus = document.getElementById("locationStatus");

    if (locationStatus) {
        locationStatus.textContent = payload.osm_error
            ? `Showing FoodSprint catalog results around ${payload.city}. OpenStreetMap fetch is temporarily unavailable.`
            : `Showing nearby restaurants around ${payload.city}.`;
    }

    if (list) {
        if (!payload.restaurants.length) {
            list.innerHTML = '<p class="mini-cart-empty">No nearby restaurants matched this filter.</p>';
        } else {
            list.innerHTML = payload.restaurants
                .slice(0, 6)
                .map(
                    (place, index) => `
                        <a class="review-card ${index === 0 ? "nearest-restaurant-card" : ""}" href="${place.url || "#map-discovery"}">
                            <div class="review-top">
                                <strong>${place.name}</strong>
                                <span>${place.distance_km.toFixed(1)} km</span>
                            </div>
                            <p>${formatPlaceSubtitle(place) || "OpenStreetMap nearby place"}</p>
                        </a>
                    `
                )
                .join("");
        }
    }

    if (cards) {
        cards.innerHTML = payload.restaurants.length
            ? payload.restaurants.map((place, index) => buildNearbyCard(place, index === 0)).join("")
            : '<div class="empty-state"><h3>No nearby places found</h3><p>Try changing the distance, type, or keyword filter.</p></div>';
    }
}

function ensureLeafletMap(fallbackLat, fallbackLng) {
    const mapContainer = document.getElementById("restaurantMap");
    if (!mapContainer || !window.L) return null;
    if (nearbyState.map) return nearbyState.map;

    nearbyState.map = L.map("restaurantMap", { zoomControl: true }).setView([fallbackLat, fallbackLng], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(nearbyState.map);
    nearbyState.clusterLayer = L.markerClusterGroup();
    nearbyState.map.addLayer(nearbyState.clusterLayer);
    return nearbyState.map;
}

function updateUserMarker(lat, lon) {
    if (!nearbyState.map || !window.L) return;
    if (!nearbyState.userMarker) {
        nearbyState.userMarker = L.circleMarker([lat, lon], {
            radius: 8,
            color: "#ffffff",
            weight: 2,
            fillColor: "#fc8019",
            fillOpacity: 1,
        }).addTo(nearbyState.map).bindPopup("You are here");
    } else {
        nearbyState.userMarker.setLatLng([lat, lon]);
    }
}

function renderRestaurantMarkers(places) {
    if (!nearbyState.map || !nearbyState.clusterLayer || !window.L) return;
    nearbyState.clusterLayer.clearLayers();

    places.forEach((place) => {
        const popupContent = `
            <div class="map-popup">
                <strong>${place.name}</strong><br>
                <span>${formatPlaceSubtitle(place) || "Nearby place"}</span><br>
                <span>${place.distance_km.toFixed(1)} km away</span>
                ${place.url ? `<br><a href="${place.url}">Open restaurant</a>` : ""}
            </div>
        `;
        const marker = L.marker([place.lat, place.lon]).bindPopup(popupContent);
        nearbyState.clusterLayer.addLayer(marker);
    });
}

function readNearbyFilters() {
    return {
        city: document.getElementById("cityFilter")?.value || "",
        type: document.getElementById("typeFilter")?.value || "",
        keyword: document.getElementById("nearbyKeyword")?.value || "",
        maxDistanceKm: document.getElementById("distanceFilter")?.value || "10",
        minRating: document.getElementById("ratingFilter")?.value || "",
    };
}

async function loadNearbyRestaurants(lat, lon, cityOverride = "") {
    const filters = readNearbyFilters();
    const params = new URLSearchParams({
        user_lat: String(lat),
        user_lon: String(lon),
        limit: "12",
        max_distance_km: filters.maxDistanceKm,
    });

    if (nearbyState.currentFoodType) params.set("food_type", nearbyState.currentFoodType);
    if (filters.type) params.set("type", filters.type);
    if (filters.keyword) params.set("keyword", filters.keyword);
    if (filters.minRating) params.set("min_rating", filters.minRating);
    if (cityOverride || filters.city) params.set("city", cityOverride || filters.city);

    const response = await fetch(`/api/nearby-restaurants?${params.toString()}`);
    if (!response.ok) {
        throw new Error("Unable to load nearby restaurants.");
    }

    const payload = await response.json();
    nearbyState.currentLat = payload.user_lat;
    nearbyState.currentLon = payload.user_lon;

    renderNearbyRestaurants(payload);
    if (nearbyState.map) {
        nearbyState.map.setView([payload.user_lat, payload.user_lon], 13);
        updateUserMarker(payload.user_lat, payload.user_lon);
        renderRestaurantMarkers(payload.restaurants);
    }
}

function getBrowserLocation(onSuccess, onFailure) {
    if (!navigator.geolocation) {
        onFailure();
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (position) => onSuccess(position.coords.latitude, position.coords.longitude),
        onFailure,
        { enableHighAccuracy: true, timeout: 9000, maximumAge: 300000 }
    );
}

function initMapDiscovery() {
    const section = document.getElementById("map-discovery");
    if (!section || nearbyState.initialized) return;
    nearbyState.initialized = true;

    const fallbackLat = Number(section.dataset.fallbackLat);
    const fallbackLng = Number(section.dataset.fallbackLng);
    const fallbackCity = section.dataset.fallbackCity || "Hyderabad";
    ensureLeafletMap(fallbackLat, fallbackLng);

    const runLoad = (lat, lon) => loadNearbyRestaurants(lat, lon).catch((error) => console.error(error));

    getBrowserLocation(
        (lat, lon) => runLoad(lat, lon),
        () => {
            const status = document.getElementById("locationStatus");
            if (status) {
                status.textContent = `Location permission denied, so FoodSprint is showing results near ${fallbackCity}.`;
            }
            runLoad(fallbackLat, fallbackLng);
        }
    );

    document.querySelectorAll("[data-food-filter]").forEach((button) => {
        button.addEventListener("click", async () => {
            document.querySelectorAll("[data-food-filter]").forEach((chip) => chip.classList.remove("active"));
            button.classList.add("active");
            nearbyState.currentFoodType = button.dataset.foodFilter || "";
            await loadNearbyRestaurants(
                nearbyState.currentLat ?? fallbackLat,
                nearbyState.currentLon ?? fallbackLng
            );
        });
    });

    ["cityFilter", "typeFilter", "distanceFilter", "ratingFilter"].forEach((id) => {
        document.getElementById(id)?.addEventListener("change", async () => {
            await loadNearbyRestaurants(
                nearbyState.currentLat ?? fallbackLat,
                nearbyState.currentLon ?? fallbackLng
            );
        });
    });

    document.getElementById("nearbyKeyword")?.addEventListener("input", async (event) => {
        clearTimeout(event.target._foodsprintTimer);
        event.target._foodsprintTimer = setTimeout(async () => {
            await loadNearbyRestaurants(
                nearbyState.currentLat ?? fallbackLat,
                nearbyState.currentLon ?? fallbackLng
            );
        }, 250);
    });

    document.getElementById("locateMeButton")?.addEventListener("click", () => {
        getBrowserLocation(
            (lat, lon) => loadNearbyRestaurants(lat, lon).catch((error) => console.error(error)),
            () => {
                const status = document.getElementById("locationStatus");
                if (status) {
                    status.textContent = `Location permission denied, continuing with ${fallbackCity}.`;
                }
                loadNearbyRestaurants(fallbackLat, fallbackLng, fallbackCity).catch((error) => console.error(error));
            }
        );
    });
}

navSearch?.addEventListener("input", (event) => {
    filterRestaurantCards(event.target.value);
});

window.addEventListener("scroll", updateHeaderState);
document.addEventListener("DOMContentLoaded", () => {
    updateHeaderState();
    installCartHandlers();
    refreshCartState().catch(() => {});
    initMapDiscovery();
});
