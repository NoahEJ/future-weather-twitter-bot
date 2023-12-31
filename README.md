# Weather Forecast Twitter Bot

## TL;DR

Every day, this script tweets the expected weather for Toronto for a date that's exactly *one year* in the future. Check it out in action [@futureweatherTO](https://twitter.com/futureweatherTO)!

## How It Works

*Image coming soon*

This Python project first pings the [Open Weather Maps](https://en.wikipedia.org/wiki/OpenWeatherMap) API for the weather forecast for a date one year in the future. Is this data reliable? Well, I'm not sure! Might need to come back in a year to see how these predictions hold up 👀

It then processes the response and creates a string describing the weather for that specific date.

Next, it connects to Twitter's API to post that string as a Tweet!

This script is hosted as an AWS Lambda function and is scheduled to run every morning via AWS EventBridge.
