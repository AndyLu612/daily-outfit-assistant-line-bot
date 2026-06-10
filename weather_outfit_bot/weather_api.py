import json
import urllib.parse
import urllib.request

from .advice import WeatherInfo


MOCK_WEATHER = WeatherInfo(
    city="台中市",
    weather="多雲午後短暫陣雨",
    min_temp=25,
    max_temp=31,
    rain_probability=60,
    comfort="悶熱",
)


class WeatherApi:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_forecast(self, city: str) -> WeatherInfo:
        if not self.api_key:
            return WeatherInfo(
                city=city,
                weather=MOCK_WEATHER.weather,
                min_temp=MOCK_WEATHER.min_temp,
                max_temp=MOCK_WEATHER.max_temp,
                rain_probability=MOCK_WEATHER.rain_probability,
                comfort=MOCK_WEATHER.comfort,
            )

        query = urllib.parse.urlencode(
            {
                "Authorization": self.api_key,
                "locationName": city,
            }
        )
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?{query}"
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        locations = payload.get("records", {}).get("location", [])
        if not locations:
            raise ValueError(f"找不到 {city} 的天氣資料")

        elements = {item["elementName"]: item["time"][0]["parameter"] for item in locations[0]["weatherElement"]}
        return WeatherInfo(
            city=city,
            weather=elements.get("Wx", {}).get("parameterName", "未知"),
            min_temp=int(elements.get("MinT", {}).get("parameterName", 0)),
            max_temp=int(elements.get("MaxT", {}).get("parameterName", 0)),
            rain_probability=int(elements.get("PoP", {}).get("parameterName", 0)),
            comfort=elements.get("CI", {}).get("parameterName", ""),
        )
