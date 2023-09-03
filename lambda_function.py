import datetime
import random
from requests_oauthlib import OAuth1Session
from dateutil.relativedelta import relativedelta
import json
import requests
import os
import boto3

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
weather_api_key = os.environ.get("WEATHER_API_KEY")
s3_bucket_name = os.environ.get("S3_BUCKET_NAME")

s3 = boto3.client('s3')
flag_file_name = 'tweet_posted_flag.txt'

def create_oauth_session():
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    return resource_owner_key, resource_owner_secret, oauth

def fetch_and_save_tokens(oauth, resource_owner_key, resource_owner_secret):
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    with open("access_tokens.json", "w") as f:
        json.dump(oauth_tokens, f)

    return oauth_tokens["oauth_token"], oauth_tokens["oauth_token_secret"]

def send_tweet(message):
    payload = {"text": message}
    resource_owner_key, resource_owner_secret, oauth = create_oauth_session()

    # Keep this try/except block uncommented only if running locally. If running in Lambda, you need to pass in the access tokens and secrets directly.
    try:
        with open("access_tokens.json", "r") as f:
            tokens = json.load(f)
            access_token = tokens["oauth_token"]
            access_token_secret = tokens["oauth_token_secret"]
    except FileNotFoundError:
        access_token, access_token_secret = fetch_and_save_tokens(oauth, resource_owner_key, resource_owner_secret)

    oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

    # Post the Tweet
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    json_response = response.json()
    print("Response code: {}".format(response.status_code))
    print(json.dumps(json_response, indent=4, sort_keys=True))
    return response.status_code

def get_weather(dateForWeather, latitudeToronto, longitudeToronto):
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall/day_summary?lat={latitudeToronto}&lon={longitudeToronto}&date={dateForWeather}&appid={weather_api_key}&units=metric")
    print(response.json())
    return response.json()

def weatherToString(weather):

    # Average temperatures per month in Toronto, in Celsius
    torontoHighs = {"January": -1, "February": -1, "March": 4, "April": 11, "May": 17, "June": 22, "July": 25, "August": 24, "September": 20, "October": 13, "November": 7, "December": 2}
    torontoLows = {"January": -8, "February": -7, "March": -3, "April": 3, "May": 9, "June": 14, "July": 17, "August": 17, "September": 13, "October": 7, "November": 1, "December": -4}

    # Different ways to describe the weather!
    lotsOfRain = ["Remember to bring that umbrella! ☔️", "Don't forget that rain jacket! 🌧️", "Bring those rain boots! 🌧️"]
    lotsOfWind = ["Don't forget that windbreaker! 💨", "Oh boy, it'll be a gusty one! 💨", "Maybe WE're the Windy City? 💨"]
    reallyHot = ["It'll be a hot one! ☀️🔥", "Sheeeesh, it'll be hot! ☀️🔥", "We're excited for this heat! ☀️🔥"]
    reallyCold = ["It's going to be a cold one! 🥶", "Make sure to really bundle up! 🥶", "Why so cooooooooold? 🧊"]
    regularDay = ["Just a regular ol' day! 😁", "Nothing out of the ordinary! 😋", "Phew, just a normal day! ☺️"]

    temperature = weather.get("temperature", {})
    min_temperature = temperature.get("min")
    max_temperature = temperature.get("max")

    precipitation = None
    if weather.get("precipitation") and weather["precipitation"].get("total"):
        precipitation = weather["precipitation"]["total"]

    wind_speed = None
    if weather.get("wind") and weather["wind"].get("max"):
        wind_speed = weather["wind"]["max"].get("speed")
    
    if min_temperature and max_temperature:
        temperatureString =  f"Temperatures will reach as high as {max_temperature}°C and as low as {min_temperature}°C."

    try:
        precipitation = float(precipitation)
    except TypeError:
        precipitation = 0

    if precipitation > 0:
        precipitationString = f"We can expect as much as {precipitation} cm of precipitation"
    else:
        precipitationString = "Don't expect any precipitation"

  
    try:
        wind_speed = float(wind_speed)
    except TypeError:
        wind_speed = 0
    if wind_speed > 0:
        windString = f", and wind speeds will reach as high as {wind_speed} km/h!"
    else:
        windString = ", and we're looking at a day of no wind."
    

    finalLineNum = random.randint(0, 2)
    currentMonth = datetime.datetime.now().strftime("%B")

    if precipitation > 25:
        finalLine = lotsOfRain[finalLineNum]
    elif wind_speed > 25:
        finalLine = lotsOfWind[finalLineNum]
    elif max_temperature and max_temperature > torontoHighs[currentMonth] + 4:
        finalLine = reallyHot[finalLineNum]
    elif min_temperature and min_temperature < torontoLows[currentMonth] - 4:
        finalLine = reallyCold[finalLineNum]
    else:
        finalLine = regularDay[finalLineNum]

    return f"{temperatureString} {precipitationString}{windString}\n\n{finalLine}"


def getIntroString():
    introStrings = ["Good morning, Toronto!", "'Ello, Toronto!", "G'day, Toronto!", "Hey there, Toronto!", "What's up, Toronto?", "Howdy, Toronto!", "Bonjour, Toronto!", "Hola, Toronto!"]
    randomNum = random.randint(0, 7)
    return introStrings[randomNum]

def main():
    dateToday = datetime.datetime.now()
    dateOneYearLater = dateToday + relativedelta(years=1)
    
    dateForWeather = dateOneYearLater.strftime("%Y-%m-%d")
    latitudeToronto = "43.6534"
    longitudeToronto = "-79.383973"

    dateNextYearForTwitter = dateOneYearLater.strftime("%b. %d, %Y")

    weather = get_weather(dateForWeather, latitudeToronto, longitudeToronto)
    weatherString = weatherToString(weather)

    introString = getIntroString()
    message = introString + " Here is your forecast for " + dateNextYearForTwitter + ":\n\n" + weatherString
    
    response_status = send_tweet(message)
    return response_status

def get_date_from_s3():
    try:
        obj = s3.get_object(Bucket=s3_bucket_name, Key=flag_file_name)
        last_date = obj['Body'].read().decode('utf-8').strip()
        return last_date
    except Exception as e:
        return None

def set_date_in_s3(current_date):
    s3.put_object(Body=current_date, Bucket=s3_bucket_name, Key=flag_file_name)

def lambda_handler(event, context):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    last_date = get_date_from_s3()
    response_status = 201
    if last_date != today:
        set_date_in_s3(today)
        response_status = main()

    if response_status != 201:
        return {
        'statusCode': response_status,
        'body': "Something went wrong!"
    }
     
    return {
        'statusCode': 201,
        'body': 'Success!'
    }

main()