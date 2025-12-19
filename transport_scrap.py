import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict
import json
import re


class TransportScrap:
    def __init__(self):
        file_path = "data/busdata.json"
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_district_from_autocomplete(self, address, lang="en"):
        url = f"https://api.geoapify.com/v1/geocode/autocomplete?text={address}&type=amenity&limit=5&lang={lang}&filter=countrycode%3Auz&format=json&apiKey=4cd051c02aab4d0898bbdc68355a9e62"

        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(url, headers=headers)
        resp = resp.json()
        try:
            return resp["results"][0]["county"]
        except Exception as e:
            return None

    def get_district_from_address(self, address, lang="en", tash_in_address=False):
        if address == "" or address is None:
            return None
        if not tash_in_address:
            address = address + ", Tashkent"
        url = f"https://api.geoapify.com/v1/geocode/search?lang={lang}&filter=countrycode:uz&text={address}&apiKey=4cd051c02aab4d0898bbdc68355a9e62"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(url, headers=headers)
        resp = resp.json()
        try:
            for row in resp["features"]:
                if row["properties"]["city"] == "Tashkent":
                    result = re.sub(r'\bdistrict\b', '', row["properties"]["county"], flags=re.IGNORECASE).strip()
                    return result
            if not resp["features"]:
                result = self.get_district_from_autocomplete(address)
                if result:
                    result = re.sub(r'\bdistrict\b', '', result, flags=re.IGNORECASE).strip()
                    return result
                return None
        except Exception as e:
            result = self.get_district_from_autocomplete(address)
            if result:
                result = re.sub(r'\bdistrict\b', '', result, flags=re.IGNORECASE).strip()
                return result
            return None

    def get_district_hh(self, address):
        return self.get_district_from_address(address, "en", True)

    def get_transport_data(self):
        df = pd.DataFrame(self.data)
        # Split into two columns
        df[["start_address", "stop_address"]] = (
            df["Yonalishnomi"]
            .str.split("-", n=1, expand=True)
            .apply(lambda x: x.str.strip())
        )
        df["start_district"] = df["start_address"].apply(self.get_district_from_address)
        df["stop_district"] = df["stop_address"].apply(self.get_district_from_address)
        return df

    def get_location_for_job(self, input_df, location_col):
        input_df["District"] = input_df[location_col].apply(self.get_district_hh)
        return input_df




