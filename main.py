import os
import json
import tweepy
import pendulum
import requests
import tempfile

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

# Tentative de conversion de la réponse en JSON
try:
    data = response.json()
    threads = data.get("threads", {})
    anecdotes = data.get("anecdotes", {})
except json.JSONDecodeError as e:
    print("Erreur lors de la conversion de la réponse en JSON :")
    print(e)
    exit(1)

# Initialiser le fuseau horaire pour la comparaison
now = pendulum.now("Europe/Paris")

# Fonction pour télécharger l'image et retourner le chemin du fichier temporaire
def download_image(image_url):
    image_url = image_url.strip()
    if not image_url:
        return None
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image : {e}, URL: {image_url}")
        return None

# Publier les anecdotes
if anecdotes:
    for date, anecdote in anecdotes.items():
        anecdote_text = anecdote.get("text", "")
        image_urls = anecdote.get("imageUrls", [])
        choices = anecdote.get("choices", [])
        duration = anecdote.get("duration", 0)
        poll_options = [choice for choice in choices if choice]

        anecdote_time = pendulum.parse(date).in_tz("Europe/Paris")

        if anecdote_time < now:
            if poll_options and duration > 0:
                client_v2.create_tweet(text=anecdote_text, poll_options=poll_options, poll_duration_minutes=duration)
            elif anecdote_text:
                media_ids = []
                for image_url in image_urls:
                    if image_url.strip():
                        image_path = download_image(image_url.strip())
                        if image_path:
                            media = api_v1.media_upload(image_path)
                            media_ids.append(media.media_id_string)
                            os.remove(image_path)

                if media_ids:
                    client_v2.create_tweet(text=anecdote_text, media_ids=media_ids)
                else:
                    client_v2.create_tweet(text=anecdote_text)

# Publier les tweets
keys_to_remove = []

for time, tweets_dict in threads.items():
    try:
        tweet_time = pendulum.parse(time).in_tz("Europe/Paris")

        if tweet_time < now:
            prev_tweet_id = None
            for index in range(1, 11):
                tweet_text = tweets_dict.get(f"Tweet{index}", "")
                image_urls = tweets_dict.get(f"Image{index}", [])
                media_ids = []

                for image_url in image_urls:
                    if image_url.strip():
                        image_path = download_image(image_url.strip())
                        if image_path:
                            media = api_v1.media_upload(image_path)
                            media_ids.append(media.media_id_string)
                            os.remove(image_path)

                if index == 1:
                    if tweet_text:
                        prev_tweet = client_v2.create_tweet(text=tweet_text, media_ids=media_ids if media_ids else None)
                        prev_tweet_id = prev_tweet.data["id"]
                    elif media_ids:
                        prev_tweet = client_v2.create_tweet(media_ids=media_ids)
                        prev_tweet_id = prev_tweet.data["id"]
                else:
                    if tweet_text:
                        prev_tweet = client_v2.create_tweet(text=tweet_text, media_ids=media_ids if media_ids else None, in_reply_to_tweet_id=prev_tweet_id)
                        prev_tweet_id = prev_tweet.data["id"]
                    elif media_ids:
                        prev_tweet = client_v2.create_tweet(media_ids=media_ids, in_reply_to_tweet_id=prev_tweet_id)
                        prev_tweet_id = prev_tweet.data["id"]

            keys_to_remove.append(time)

    except Exception as e:
        print(f"Erreur lors du traitement du thread à l'heure {time} : {e}")

# Supprimer les clés après l'itération
for key in keys_to_remove:
    threads.pop(key)

# Enregistrer les tweets restants dans le fichier JSON
with open("tweet.json", "w") as file:
    json.dump(threads, file)
