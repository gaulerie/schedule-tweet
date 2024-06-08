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
url = "https://script.google.com/macros/s/AKfycbxsMMZ9NUfqzRtuaiNzpiYB1V45XgzTBRCCk9kbDAo-ZydZGcQLf3ANrujn0pY_KJBn/exec"
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
    print("Données JSON récupérées :")
    print(json.dumps(data, indent=4))  # Afficher les données JSON de manière lisible
    threads = data.get("threads", {})
    anecdotes = data.get("anecdotes", {})
except json.JSONDecodeError as e:
    print("Erreur lors de la conversion de la réponse en JSON :")
    print(e)
    exit(1)

# Afficher les données reçues pour débogage
print("Threads reçus :")
print(json.dumps(threads, indent=4))

print("Anecdotes reçues :")
print(json.dumps(anecdotes, indent=4))

# Initialiser le fuseau horaire
now = pendulum.now("Europe/Paris")

# Publier les anecdotes
if anecdotes:
    print("Traitement des anecdotes:")
    for date, anecdote in anecdotes.items():
        anecdote_text = anecdote.get("text", "")
        image_url = anecdote.get("imageUrl", "")
        choices = anecdote.get("choices", [])
        duration = anecdote.get("duration", 0)
        poll_options = [choice for choice in choices if choice]

        if anecdote_text:
            if image_url:
                print("Publication d'une anecdote avec image:")
                print(f"Texte: {anecdote_text}, Image URL: {image_url}")
                media = api_v1.media_upload(image_url)
                client_v2.create_tweet(text=anecdote_text, media_ids=[media.media_id_string])
            elif poll_options and duration > 0:
                print("Publication d'une anecdote avec sondage:")
                print(f"Texte: {anecdote_text}, Options: {poll_options}, Durée: {duration}")
                client_v2.create_tweet(text=anecdote_text, poll_options=poll_options, poll_duration_minutes=duration)
            else:
                print("Publication d'une anecdote sans image ni sondage:")
                print(f"Texte: {anecdote_text}")
                client_v2.create_tweet(text=anecdote_text)

# Publier les tweets
keys_to_remove = []

for time, tweets_dict in threads.items():
    try:
        # Supprimer la partie en parenthèses de la chaîne de date
        time_without_parens = time.split(' (')[0]
        # Analyser la chaîne de date et la convertir en un objet pendulum
        tweet_time = datetime.strptime(time_without_parens, '%a %b %d %Y %H:%M:%S %Z%z')
        tweet_time = pendulum.instance(tweet_time)
    except ValueError as e:
        print(f"Erreur lors de l'analyse de la date : {e}")
        continue

    if tweet_time < now:
        prev_tweet_id = None
        for index in range(1, 11):
            tweet_text = tweets_dict.get(f"Tweet{index}", "")
            image_path = tweets_dict.get(f"Image{index}", "")
            unique_tweet_text = f"{tweet_text} - {uuid.uuid4()}"
            if index == 1:
                if tweet_text and image_path:
                    print(f"Publication du premier tweet avec image: {tweet_text}, Image: {image_path}")
                    media = api_v1.media_upload(image_path)
                    prev_tweet = client_v2.create_tweet(
                        text=unique_tweet_text, media_ids=[media.media_id_string]
                    )
                    prev_tweet_id = prev_tweet.data["id"]
                    os.remove(image_path)
                elif tweet_text:
                    print(f"Publication du premier tweet sans image: {tweet_text}")
                    prev_tweet = client_v2.create_tweet(text=unique_tweet_text)
                    prev_tweet_id = prev_tweet.data["id"]
                elif image_path:
                    print(f"Publication d'une image sans texte: {image_path}")
                    media = api_v1.media_upload(image_path)
                    prev_tweet = client_v2.create_tweet(media_ids=[media.media_id_string])
                    prev_tweet_id = prev_tweet.data["id"]
                    os.remove(image_path)
            else:
                if tweet_text and image_path:
                    print(f"Publication d'un tweet de suivi avec image: {tweet_text}, Image: {image_path}")
                    media = api_v1.media_upload(image_path)
                    prev_tweet = client_v2.create_tweet(
                        text=unique_tweet_text,
                        media_ids=[media.media_id_string],
                        in_reply_to_tweet_id=prev_tweet_id,
                    )
                    prev_tweet_id = prev_tweet.data["id"]
                    os.remove(image_path)
                elif tweet_text:
                    print(f"Publication d'un tweet de suivi sans image: {tweet_text}")
                    prev_tweet = client_v2.create_tweet(
                        text=unique_tweet_text,
                        in_reply_to_tweet_id=prev_tweet_id,
                    )
                    prev_tweet_id = prev_tweet.data["id"]
                elif image_path:
                    print(f"Publication d'une image de suivi sans texte: {image_path}")
                    media = api_v1.media_upload(image_path)
                    prev_tweet = client_v2.create_tweet(
                        media_ids=[media.media_id_string],
                        in_reply_to_tweet_id=prev_tweet_id,
                    )
                    prev_tweet_id = prev_tweet.data["id"]
                    os.remove(image_path)
        keys_to_remove.append(time)

# Supprimer les clés après l'itération
for key in keys_to_remove:
    threads.pop(key)

# Enregistrer les tweets restants dans le fichier JSON
with open("tweet.json", "w") as file:
    json.dump(threads, file)
