# FoodSprint Project Prompts for PPT Screenshots

## Prompt 1: Full Base Project

```text
Build a full-stack, production-ready food delivery web application using Flask named "FoodSprint".

Requirements:
- modern Swiggy/Zomato-style UI
- user signup, login, logout
- restaurant listing with cards
- unique menu for each restaurant
- add to cart, remove from cart, quantity update
- checkout flow
- order system
- responsive design
- SQLite/PostgreSQL support
- clean modular code structure
- do not use static boring UI, make it modern and polished
```

## Prompt 2: Admin, Staff, Payment, and Order Tracking

```text
Enhance my existing FoodSprint app without removing any features.

Add:
- single admin system
- admin dashboard
- max 3 staff accounts with staff_id like STF001
- staff login and staff dashboard
- staff can update order status only
- order status flow:
  PLACED
  PREPARING
  OUT_FOR_DELIVERY
  DELIVERED
- UPI QR payment simulation
- admin can set UPI ID
- payment confirmation should generate transaction ID
- user order tracking timeline page
- secure password hashing
- session-based authentication
```

## Prompt 3: AI Recommendation System

```text
Enhance my existing FoodSprint app with AI-based recommendation features.

Add:
- diet recommendation system for
  weight loss
  muscle gain
  balanced diet
  vegetarian
- show recommended foods and foods to avoid
- show calories
- add smart tags like:
  Healthy
  High Protein
  Low Calorie
  Popular
- track user order history
- recommend foods based on past behavior
- keep the logic simple, explainable, and modular
- do not break existing app features
```

## Prompt 4: Map-Based Restaurant Discovery with OpenStreetMap

```text
Enhance my existing Flask-based FoodSprint app by adding a nearby restaurant finder without using Google Maps API.

Requirements:
- use OpenStreetMap tiles
- use Leaflet.js on frontend
- use Overpass API on backend
- detect browser location
- fallback to Hyderabad if location permission is denied
- show nearby restaurants on the map
- add marker clustering
- clicking a marker should show restaurant details
- add filters for city, type, keyword, distance, rating, veg/non-veg
- keep all existing FoodSprint features working
```
