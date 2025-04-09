"""
Configuration file for app categories used in the PowerGuard system.
This defines which apps are considered critical for different usage categories.
"""

APP_CATEGORIES = {
    "messaging": {
        "com.whatsapp": "WhatsApp",
        "com.facebook.orca": "Messenger",
        "com.viber.voip": "Viber"
    },
    "navigation": {
        "com.google.android.apps.maps": "Google Maps",
        "com.waze": "Waze",
        "com.mapbox.app": "Mapbox"
    },
    "email": {
        "com.google.android.gm": "Gmail",
        "com.microsoft.office.outlook": "Outlook",
        "com.yahoo.mobile.client.android.mail": "Yahoo Mail"
    },
    "social": {
        "com.facebook.katana": "Facebook", 
        "com.twitter.android": "Twitter",
        "com.instagram.android": "Instagram",
        "com.snapchat.android": "Snapchat"
    },
    "media": {
        "com.spotify.music": "Spotify",
        "com.netflix.mediaclient": "Netflix",
        "com.google.android.youtube": "YouTube",
        "com.pandora.android": "Pandora"
    }
}

# Flattened mapping for quick package name lookups
PACKAGE_TO_NAME = {}
PACKAGE_TO_CATEGORY = {}

for category, apps in APP_CATEGORIES.items():
    for package, name in apps.items():
        PACKAGE_TO_NAME[package] = name
        PACKAGE_TO_CATEGORY[package] = category

def get_app_category(package_name: str) -> str:
    """Get the category for a given package name."""
    return PACKAGE_TO_CATEGORY.get(package_name.lower(), None)

def get_app_name(package_name: str) -> str:
    """Get the friendly name for a given package name."""
    return PACKAGE_TO_NAME.get(package_name.lower(), package_name)

def get_apps_in_category(category: str) -> dict:
    """Get all apps in a given category."""
    return APP_CATEGORIES.get(category.lower(), {}) 