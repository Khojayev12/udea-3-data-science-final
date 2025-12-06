# my google maps api key: AIzaSyA3runJi0uovu7bEOL7E2HytrXXuHFqvOk
# my yandex maps api key: 55277417-19a9-49ce-aa58-4e5a3941417f

import requests

def get_district_from_yandex(address: str, api_key: str):
    """
    Returns the district (Administrative Area Level 2) for a given address
    using Yandex Geocoder API.
    """

    url = "https://geocode-maps.yandex.ru/v1/"
    params = {
        "apikey": api_key,
        "geocode": address,
        "format": "json",
        "lang": "uz_UZ"  # use Uzbek language
    }

    response = requests.get(url, params=params)
    data = response.json()
    #print(data)

    try:
        components = (
            data["response"]["GeoObjectCollection"]["featureMember"][0]
            ["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]
            ["Address"]["Components"]
        )

        # Look for second-level administrative division (district / tuman)
        for c in components:
            if c["kind"] in ("district", "area"):
                return c["name"]

        return "District not found"

    except (KeyError, IndexError):
        return "Address not found"


# -------------------------
# USAGE EXAMPLE
# -------------------------
YANDEX_API_KEY = "55277417-19a9-49ce-aa58-4e5a3941417f"

address = "Sputnik 16A 17 Toshkent"

district = get_district_from_yandex(address, YANDEX_API_KEY)
print("District:", district)

address = "Boshliq mavzesi, Tashkent"

district = get_district_from_yandex(address, YANDEX_API_KEY)
print("District:", district)

address = "Qo‘yliq 1-mavzesi, Tashkent"
district = get_district_from_yandex(address, YANDEX_API_KEY)
print("District:", district)