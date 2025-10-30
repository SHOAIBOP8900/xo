from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

TOKEN = "a2i0V--xUAUkC-skFTzuIe9zzoEqn8PKwfmQWYJBUC9Z9o3wbV9z7_TQp7w5FQi1"

def safe_first(lst, key=None):
    if lst and len(lst) > 0:
        return lst[0].get(key) if key else lst[0]
    return None

def fetch_truecaller(number):
    url = f"https://search5-noneu.truecaller.com/v2/search?q={number}&countryCode=IN&type=4&encoding=json"
    headers = {
        "User-Agent": "Truecaller/15.32.6 (Android;14)",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {TOKEN}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        info = data.get("data", [{}])[0]

        return {
            "source": "primary",
            "name": info.get("name"),
            "phone": safe_first(info.get("phones"), "e164Format"),
            "carrier": safe_first(info.get("phones"), "carrier"),
            "email": safe_first(info.get("internetAddresses"), "id"),
            "gender": info.get("gender"),
            "city": safe_first(info.get("addresses"), "city"),
            "country": safe_first(info.get("addresses"), "countryCode"),
            "image": info.get("image"),
            "isFraud": info.get("isFraud", False)
        }

    except requests.exceptions.HTTPError as e:
        if res.status_code in [404, 429]:
            return fetch_backup(number)
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def fetch_backup(number):
    """Backup request to ads-segment-profile endpoint"""
    try:
        url = f"https://ads-segment-profile-noneu.truecaller.com/v1/ads/keywords"
        params = {
            "adId": "55695669-192c-4a2b-aba2-3793ce0de287",
            "placement": "DETAILS_BOTTOM",
            "q": number,
            "optOutUser": "false",
            "encoding": "json"
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; TECNO KI8 Build/TP1A.220624.014; wv) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
                          "Chrome/141.0.7390.97 Mobile Safari/537.36",
            "Accept-Encoding": "gzip",
            "If-Modified-Since": "Tue, 28 Oct 2025 07:54:28 GMT"
        }

        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        return {
            "source": "backup",
            "ads_keywords": data.get("keywords", []),
            "ad_meta": data.get("meta", {}),
            "note": "Backup endpoint used due to rate limit or missing data"
        }

    except Exception as e:
        return {"error": f"Backup request failed: {str(e)}"}


@app.route("/truecaller", methods=["GET"])
def truecaller_api():
    number = request.args.get("number")
    if not number:
        return jsonify({"error": "Missing number parameter"}), 400
    result = fetch_truecaller(number)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
