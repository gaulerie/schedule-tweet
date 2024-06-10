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

# Initialiser le fuseau horaire pour la comparaison
now = pendulum.now("Europe/Paris")
print(f"Current time (Europe/Paris): {now}")

# Fonction pour télécharger l'image et retourner le chemin du fichier temporaire
def download_image(image_url):
    try:
        response = requests.get(image_url.strip())
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image : {e}")
        return None

# Fonction pour marquer les entrées comme tweeté
def mark_as_tweeted(thread_updates, anecdote_updates):
    update_url = "https://script.google.com/macros/s/AKfycbxsMMZ9NUfqzRtuaiNzpiYB1V45XgzTBRCCk9kbDAo-ZydZGcQLf3ANrujn0pY_KJBn/exec"
    data = {
        "threads": thread_updates,
        "anecdotes": anecdote_updates
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(update_url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        print(f"Erreur lors de la mise à jour des données : {response.status_code}")
        print(response.text)
    else:
        print("Données mises à jour avec succès")

# Publier les anecdotes
anecdote_updates = []
if anecdotes:
    print("Traitement des anecdotes:")
    for rowIndex, (date, anecdote) in enumerate(anecdotes.items(), start=1):
        anecdote_text = anecdote.get("text", "").strip()
        image_urls = anecdote.get("imageUrl", "").strip().split(", ")
        choices = [choice for choice in anecdote.get("choices", []) if choice.strip()]
        duration = anecdote.get("duration", 0)

        # Vérifier que l'anecdote a un texte ou des images valides avant de la publier
        if not anecdote_text and not image_urls:
            print("Aucune anecdote valide trouvée.")
            continue

        # Convertir la date de l'anecdote en Europe/Paris pour comparaison
        anecdote_time = pendulum.parse(date).in_tz("Europe/Paris")
        print(f"Anecdote time (Europe/Paris) : {anecdote_time}")
        print(f"Comparaison anecdote: Anecdote time: {anecdote_time}, Current time: {now}")

        if anecdote_time < now:
            if anecdote_text:
                media_ids = []
                for image_url in image_urls:
                    if image_url:
                        image_path = download_image(image_url)
                        if image_path:
                            media = api_v1.media_upload(image_path)
                            media_ids.append(media.media_id_string)
                            os.remove(image_path)
                if media_ids and not (choices and duration > 0):
                    print(f"Publication d'une anecdote avec images: {anecdote_text}, Images: {image_urls}")
                    client_v2.create_tweet(text=anecdote_text, media_ids=media_ids)
                elif choices and duration > 0:
                    print(f"Publication d'une anecdote avec sondage: {anecdote_text}, Options: {choices}, Durée: {duration}")
                    client_v2.create_tweet(text=anecdote_text, poll_options=choices, poll_duration_minutes=duration)
                else:
                    print(f"Publication d'une anecdote sans image ni sondage: {anecdote_text}")
                    client_v2.create_tweet(text=anecdote_text)
                anecdote_updates.append({"rowIndex": rowIndex})

# Publier les threads
thread_updates = []
keys_to_remove = []

for rowIndex, (time, tweets_dict) in enumerate(threads.items(), start=1):
    try:
        print(f"Traitement du thread pour l'heure : {time}")
        # Convertir l'heure du thread en Europe/Paris pour comparaison
        tweet_time = pendulum.parse(time).in_tz("Europe/Paris")
        print(f"Tweet time (Europe/Paris) : {tweet_time}, Current time (Europe/Paris) : {now}")
        print(f"Comparaison thread: Tweet time: {tweet_time}, Current time: {now}")

        if tweet_time < now:
            print(f"Le thread est prévu pour être publié.")
            prev_tweet_id = None
            for index in range(1, 11):
                tweet_text = tweets_dict.get(f"Tweet{index}", "").strip()
                image_urls = tweets_dict.get(f"Image{index}", "").strip().split(", ")
                media_ids = []

                for image_url in image_urls:
                    if image_url:
                        image_path = download_image(image_url)
                        if image_path:
                            media = api_v1.media_upload(image_path)
                            media_ids.append(media.media_id_string)
                            os.remove(image_path)

                if index == 1:
                    if tweet_text:
                        print(f"Publication du premier tweet avec images: {tweet_text}, Images: {image_urls}")
                        prev_tweet = client_v2.create_tweet(text=tweet_text, media_ids=media_ids if media_ids else None)
                        prev_tweet_id = prev_tweet.data["id"]
                    elif media_ids:
                        print(f"Publication du premier tweet uniquement avec des images: {image_urls}")
                        prev_tweet = client_v2.create_tweet(media_ids=media_ids)
                        prev_tweet_id = prev_tweet.data["id"]
                else:
                    if tweet_text:
                        print(f"Publication d'un tweet de suivi avec images: {tweet_text}, Images: {image_urls}")
                        prev_tweet = client_v2.create_tweet(text=tweet_text, media_ids=media_ids if media_ids else None, in_reply_to_tweet_id=prev_tweet_id)
                        prev_tweet_id = prev_tweet.data["id"]
                    elif media_ids:
                        print(f"Publication d'un tweet de suivi uniquement avec des images: {image_urls}")
                        prev_tweet = client_v2.create_tweet(media_ids=media_ids, in_reply_to_tweet_id=prev_tweet_id)
                        prev_tweet_id = prev_tweet.data["id"]

            keys_to_remove.append(time)
            thread_updates.append({"rowIndex": rowIndex})
        else:
            print(f"Le thread n'est pas encore prévu pour être publié.")
    except Exception as e:
        print(f"Erreur lors du traitement du thread à l'heure {time} : {e}")

# Supprimer les clés après l'itération
for key in keys_to_remove:
    threads.pop(key)

# Enregistrer les tweets restants dans le fichier JSON
with open("tweet.json", "w") as file:
    json.dump(threads, file)

# Marquer les tweets et anecdotes comme tweeté
mark_as_tweeted(thread_updates, anecdote_updates)
