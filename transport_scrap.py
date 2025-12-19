#https://api.geoapify.com/v1/geocode/search?text=%D0%A2%D0%B0%D1%88%D0%BA%D0%B5%D0%BD%D1%82%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%9C%D1%83%D0%BC%D0%B8%D0%BD%D0%BE%D0%B2%D0%B0%2C%2011&lang=ru&format=json&apiKey=YOUR_API_KEY
import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict
import json

#https://api.geoapify.com/v1/geocode/search?text=%D0%A2%D0%B0%D1%88%D0%BA%D0%B5%D0%BD%D1%82%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%9C%D1%83%D0%BC%D0%B8%D0%BD%D0%BE%D0%B2%D0%B0%2C%2011&lang=ru&filter=countrycode:uz&format=json&apiKey=YOUR_API_KEY


class TransportScrap:
    def __init__(self):
        file_path = "data/busdata.json"
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_district_from_autocomplete(self, address, lang="uz"):
        #address = address + ", Tashkent"
        url = f"https://api.geoapify.com/v1/geocode/autocomplete?text={address}&type=amenity&limit=5&lang={lang}&filter=countrycode%3Auz&format=json&apiKey=4cd051c02aab4d0898bbdc68355a9e62"
        #url = "https://api.geoapify.com/v1/geocode/autocomplete?text=Qo%27yliq+Dehqon+bozori&type=amenity&limit=5&lang=uz&filter=countrycode%3Auz&format=json&apiKey=YOUR_API_KEY"

        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(url, headers=headers)
        #print(resp.text)
        resp = resp.json()
        try:
            #print(resp["results"][0]["county"])
            return resp["results"][0]["county"]
        except Exception as e:
            return None

    def get_district_from_address(self, address, lang="uz"):
        if address == "" or address is None:
            return None
        address = address + ", Tashkent"
        url = f"https://api.geoapify.com/v1/geocode/search?lang={lang}&filter=countrycode:uz&text={address}&apiKey=4cd051c02aab4d0898bbdc68355a9e62"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(url, headers=headers)
        #print(resp.text)
        resp = resp.json()
        try:
            for row in resp["features"]:
                if row["properties"]["city"] == "Toshkent":
                    return row["properties"]["county"]
            if not resp["features"]:
                print("using autocomplete")
                result = self.get_district_from_autocomplete(address)
                if result:
                    return result
                return None
        except Exception as e:
            print("using autocomplete")
            result = self.get_district_from_autocomplete(address)
            if result:
                return result
            return None

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
        input_df["District"] = input_df[location_col].apply(self.get_district_from_address)
        return input_df


TransportScrap1 = TransportScrap()
#print(TransportScrap1.get_district_from_address("Food City savdo majmuasi 3", "uz"))


