import os
import json
import tweepy
import pendulum
import uuid
import requests
from datetime import datetime

# Configurer l'API v1.1 pour le téléchargement de médias
consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret_key = os.environ.get("TWITTER_CONSUMER_SECRET_KEY")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
auth.set_access_token(access_token, access_token_secret)
api_v1 = tweepy.API(auth)

# Configurer l'API v2 pour la publication de tweets
bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
client_v2 = tweepy.Client(bearer_token, consumer_key, consumer_secret_key, access_token, access_token_secret)

# Récupérer les données depuis le déploiement Google Apps Script
url = "https://script.google.com/macros/s/AKfycbzM6FbGGxxEUYEx5ZPihOROkrGHWJoVxUYbbMstv8xSJsnFD2n19AHKjwIjNBVFuStp/exec"
response = requests.get(url)

# Vérification du statut de la réponse
if response.status_code != 200:
    print(f"Erreur lors de la récupération des données : {response.status_code}")
    print(response.text)
    exit(1)

# Afficher la réponse brute pour débogage
print("Réponse brute :")
print(response.text)

# Tentative de conversion de la réponse en JSON
try:
    data = response.json()
    if "Error" in data:
        print(f"Erreur dans la réponse : {data['Error']}")
        exit(1)
    tweets = data.get("threads", {})
    anecdote_data = data.get("anecdotes", {})
except json.JSONDecodeError as e:
    print("Erreur lors de la conversion de la réponse en JSON :")
    print(e)
    exit(1)

# Initialiser le fuseau horaire
now = pendulum.now("Europe/Paris")

# Publier les anecdotes
if anecdote_data:
    anecdote_text = anecdote_data.get("text", "")
    image_url = anecdote_data.get("imageUrl", "")
    choices = anecdote_data.get("choices", [])
    duration = anecdote_data.get("duration", 0)
    poll_options = [{"label": choice} for choice in choices if choice]
    
    if anecdote_text:
        if image_url:
            media = api_v1.media_upload(image_url)
            client_v2.create_tweet(text=anecdote_text,
