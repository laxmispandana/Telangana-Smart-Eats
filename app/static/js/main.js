const grid = document.getElementById("restaurant-grid");
const searchInput = document.getElementById("search-input");
const foodFilter = document.getElementById("food-filter");
const ratingFilter = document.getElementById("rating-filter");
const healthyFilter = document.getElementById("healthy-filter");
const locationBtn = document.getElementById("location-btn");
const locationStatus = document.getElementById("location-status");

let map;
let markerLayer;
let userCoords = null;
let lastRestaurants = [];

function renderRestaurantCard(restaurant) {
    const distanceLabel = restaurant.distance !== null ? `${restaurant.distance} km away` : restaurant.city;
    const healthyBadge = restaurant.category === "diet" || restaurant.category === "veg" ? '<span class="healthy-pill">Healthy</span>' : "";
    return `
        <article class="restaurant-card">
            <img src="${restaurant.image_url}" alt="${restaurant.name}">
            <div class="restaurant-card-body">
                <div class="restaurant-meta">
                    <div>
                        <h3>${restaurant.name}</h3>
                        <p>${restaurant.area}, ${restaurant.city}</p>
                    </div>
                    <strong>⭐ ${restaurant.rating}</strong>
                </div>
                <p>${restaurant.cuisine}</p>
                <div class="nutrition-row">
                    <span class="tag">${restaurant.category}</span>
                    ${healthyBadge}
                    <span>${distanceLabel}</span>
                    <span>${restaurant.delivery_time} mins</span>
                </div>
                <p>${restaurant.description}</p>
                <div class="menu-footer">
                    <a href="/restaurants/${restaurant.id}" class="btn btn-mini">View menu</a>
                </div>
            </div>
        </article>
    `;
}

async function loadRestaurants() {
    if (!grid) return;

    const params = new URLSearchParams({
        search: searchInput?.value || "",
        food_type: foodFilter?.value || "",
        rating: ratingFilter?.value || "0",
        healthy: healthyFilter?.checked ? "true" : "false",
    });

    if (userCoords) {
        params.set("lat", userCoords.latitude);
        params.set("lng", userCoords.longitude);
    }

    const response = await fetch(`/restaurants/data?${params.toString()}`);
    const restaurants = await response.json();
    lastRestaurants = restaurants;
    grid.innerHTML = restaurants.map(renderRestaurantCard).join("") || "<p>No restaurants matched these filters.</p>";
    updateMap();
}

function initMap() {
    const mapNode = document.getElementById("map");
    if (!mapNode || map) return;

    map = L.map("map").setView([17.385, 78.4867], 6.8);
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
        if (restaurant.lat === null || restaurant.lng === null) return;
        L.marker([restaurant.lat, restaurant.lng])
            .bindPopup(`<strong>${restaurant.name}</strong><br>${restaurant.city}`)
            .addTo(markerLayer);
    });

    if (userCoords) {
        L.circleMarker([userCoords.latitude, userCoords.longitude], {
            radius: 8,
            color: "#d95d39",
            fillColor: "#d95d39",
            fillOpacity: 1,
        }).bindPopup("You are here").addTo(markerLayer);
    }
}

function requestLocation() {
    if (!navigator.geolocation) {
        if (locationStatus) locationStatus.textContent = "Geolocation is not supported in this browser.";
        return;
    }

    if (locationStatus) locationStatus.textContent = "Fetching your location and sorting by distance...";

    navigator.geolocation.getCurrentPosition(
        ({ coords }) => {
            userCoords = coords;
            if (locationStatus) locationStatus.textContent = "Location detected. Restaurants are now sorted nearest-first.";
            if (map) map.setView([coords.latitude, coords.longitude], 8);
            loadRestaurants();
        },
        () => {
            if (locationStatus) locationStatus.textContent = "Location permission denied. Showing all Telangana restaurants.";
        },
        { enableHighAccuracy: true, timeout: 8000 }
    );
}

[searchInput, foodFilter, ratingFilter, healthyFilter].forEach((node) => {
    node?.addEventListener("input", loadRestaurants);
    node?.addEventListener("change", loadRestaurants);
});

locationBtn?.addEventListener("click", requestLocation);

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    loadRestaurants();
});
