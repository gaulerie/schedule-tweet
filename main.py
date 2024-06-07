import os
import json
import tweepy
import pendulum
import uuid

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

now = pendulum.now("Asia/Dhaka")
with open("tweet.json") as file:
    tweets = json.load(file)
    for time in list(tweets):
        tweet_time = pendulum.parse(time, tz="Europe/Paris")
        if tweet_time < now:
            if len(tweets[time].keys()) == 1:
                for tweet_text, image_path in tweets[time].items():
                    unique_tweet_text = f"{tweet_text} - {uuid.uuid4()}"
                    if tweet_text and image_path:
                        media = api_v1.media_upload(image_path)
                        client_v2.create_tweet(text=unique_tweet_text, media_ids=[media.media_id_string])
                        os.remove(image_path)
                    elif tweet_text:
                        client_v2.create_tweet(text=unique_tweet_text)
                    elif image_path:
                        media = api_v1.media_upload(image_path)
                        client_v2.create_tweet(media_ids=[media.media_id_string])
                        os.remove(image_path)
            else:
                prev_tweet_id = None
                for index, (tweet_text, image_path) in enumerate(tweets[time].items()):
                    unique_tweet_text = f"{tweet_text} - {uuid.uuid4()}"
                    if index == 0:
                        if tweet_text and image_path:
                            media = api_v1.media_upload(image_path)
                            prev_tweet = client_v2.create_tweet(
                                text=unique_tweet_text, media_ids=[media.media_id_string]
                            )
                            prev_tweet_id = prev_tweet.data["id"]
                            os.remove(image_path)
                        elif tweet_text:
                            prev_tweet = client_v2.create_tweet(text=unique_tweet_text)
                            prev_tweet_id = prev_tweet.data["id"]
                        elif image_path:
                            media = api_v1.media_upload(image_path)
                            prev_tweet = client_v2.create_tweet(
                                media_ids=[media.media_id_string]
                            )
                            prev_tweet_id = prev_tweet.data["id"]
                            os.remove(image_path)
                    elif tweet_text and image_path:
                        media = api_v1.media_upload(image_path)
                        prev_tweet = client_v2.create_tweet(
                            text=unique_tweet_text,
                            media_ids=[media.media_id_string],
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                        os.remove(image_path)
                    elif tweet_text:
                        prev_tweet = client_v2.create_tweet(
                            text=unique_tweet_text,
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                    elif image_path:
                        media = api_v1.media_upload(image_path)
                        prev_tweet = client_v2.create_tweet(
                            media_ids=[media.media_id_string],
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                        os.remove(image_path)
            tweets.pop(time)

with open("tweet.json", "w") as file:
    file.write(json.dumps(tweets))
