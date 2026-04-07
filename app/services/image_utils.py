def _pexels_photo(photo_id, width=1200):
    return (
        f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg"
        f"?auto=compress&cs=tinysrgb&w={width}"
    )


RESTAURANT_IMAGE_MAP = {
    "hyderabad spice route": _pexels_photo(776538),
    "warangal millet kitchen": _pexels_photo(11433158),
    "karimnagar grill house": _pexels_photo(19127343),
    "nizamabad veggie craft": _pexels_photo(15297129),
    "khammam fit feast": _pexels_photo(33324490),
}

EXACT_MENU_IMAGE_MAP = {
    "chicken dum biryani": _pexels_photo(9738983),
    "mutton haleem bowl": "https://img.spoonacular.com/recipes/641975-556x370.jpg",
    "tandoori chicken": _pexels_photo(29173110),
    "talawa gosht": _pexels_photo(262978),
    "garlic butter naan": _pexels_photo(12737656),
    "paneer tikka": _pexels_photo(35041650),
    "green salad platter": _pexels_photo(19453404),
    "millet khichdi": _pexels_photo(1640774),
    "egg fried rice": _pexels_photo(723198),
    "double ka meetha": _pexels_photo(8042602),
    "foxtail millet bowl": _pexels_photo(1640774),
    "protein idli plate": "https://img.spoonacular.com/recipes/642540-556x370.jpg",
    "grilled fish with greens": _pexels_photo(3298637),
    "low-oil chicken curry": _pexels_photo(7625056),
    "ragi dosa": _pexels_photo(32229637),
    "yogurt fruit cup": _pexels_photo(1092730),
    "peanut chutney wrap": _pexels_photo(461198),
    "power upma": _pexels_photo(4331491),
    "paneer protein bowl": _pexels_photo(1640774),
    "cold-pressed juice": _pexels_photo(96974),
    "peri peri chicken roll": _pexels_photo(461198),
    "bbq chicken wings": _pexels_photo(616354),
    "paneer shawarma": _pexels_photo(5718078),
    "veg loaded pizza": _pexels_photo(825661),
    "chicken loaded pizza": _pexels_photo(708587),
    "garlic bread": _pexels_photo(825661),
    "caesar salad": _pexels_photo(257816),
    "grilled chicken steak": _pexels_photo(410648),
    "brown rice bowl": _pexels_photo(1640774),
    "choco mousse": _pexels_photo(3026808),
    "veg thali": _pexels_photo(958545),
    "palak paneer": _pexels_photo(35041650),
    "mixed veg curry": _pexels_photo(5409010),
    "quinoa pulao": _pexels_photo(1640774),
    "masala dosa": _pexels_photo(32229637),
    "mini idli sambar": _pexels_photo(32229637),
    "curd rice": _pexels_photo(1640774),
    "tandoori broccoli": _pexels_photo(5938),
    "fruit salad": _pexels_photo(1092730),
    "badam milk": _pexels_photo(5946720),
    "lean chicken bowl": _pexels_photo(1640774),
    "tofu stir fry": _pexels_photo(1640774),
    "avocado millet salad": _pexels_photo(1640774),
    "egg white wrap": _pexels_photo(461198),
    "oats smoothie": _pexels_photo(5946720),
    "salmon rice bowl": _pexels_photo(3298637),
    "paneer burrito bowl": _pexels_photo(1640774),
    "sweet potato chaat": _pexels_photo(1640774),
    "turkey sandwich": _pexels_photo(1600711),
    "greek yogurt parfait": _pexels_photo(1092730),
}


MENU_IMAGE_MAP = [
    (("biryani", "pulao", "fried rice", "rice bowl"), _pexels_photo(9738983)),
    (("pizza", "garlic bread"), _pexels_photo(825661)),
    (("chicken", "wings", "tandoori", "turkey", "egg"), _pexels_photo(29173110)),
    (("paneer", "palak"), _pexels_photo(35041650)),
    (("dosa", "idli", "upma"), _pexels_photo(32229637)),
    (("salad", "fruit", "yogurt", "juice", "smoothie"), _pexels_photo(19453404)),
    (("millet", "quinoa", "tofu", "broccoli", "sweet potato", "oats", "avocado"), _pexels_photo(15795823)),
    (("curry", "khichdi", "thali"), _pexels_photo(35041650)),
    (("dessert", "mousse", "meetha", "milk"), _pexels_photo(8042602)),
]


def themed_food_image(query):
    normalized = query.lower()
    if normalized in EXACT_MENU_IMAGE_MAP:
        return EXACT_MENU_IMAGE_MAP[normalized]
    for keywords, image_url in MENU_IMAGE_MAP:
        if any(keyword in normalized for keyword in keywords):
            return image_url
    return _pexels_photo(15795823)


def themed_restaurant_image(query):
    normalized = query.lower()
    for restaurant_name, image_url in RESTAURANT_IMAGE_MAP.items():
        if restaurant_name in normalized:
            return image_url
    return _pexels_photo(776538)
