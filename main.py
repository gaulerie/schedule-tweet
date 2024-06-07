import os
import json
import tweepy
import pendulum

consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret_key = os.environ.get("TWITTER_CONSUMER_SECRET_KEY")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

client = tweepy.Client(bearer_token, consumer_key, consumer_secret_key, access_token, access_token_secret)

now = pendulum.now("Asia/Dhaka")
with open("tweet.json") as file:
    tweets = json.load(file)
    for time in list(tweets):
        tweet_time = pendulum.parse(time, tz="Europe/Paris")
        if tweet_time < now:
            if len(tweets[time].keys()) == 1:
                for tweet_text, image_path in tweets[time].items():
                    if tweet_text and image_path:
                        media = client.media_upload(image_path)
                        client.create_tweet(text=tweet_text, media_ids=[media.media_id])
                        os.remove(image_path)
                    elif tweet_text:
                        client.create_tweet(text=tweet_text)
                    elif image_path:
                        media = client.media_upload(image_path)
                        client.create_tweet(media_ids=[media.media_id])
                        os.remove(image_path)
            else:
                prev_tweet_id = None
                for index, (tweet_text, image_path) in enumerate(tweets[time].items()):
                    if index == 0:
                        if tweet_text and image_path:
                            media = client.media_upload(image_path)
                            prev_tweet = client.create_tweet(
                                text=tweet_text, media_ids=[media.media_id]
                            )
                            prev_tweet_id = prev_tweet.data["id"]
                            os.remove(image_path)
                        elif tweet_text:
                            prev_tweet = client.create_tweet(text=tweet_text)
                            prev_tweet_id = prev_tweet.data["id"]
                        elif image_path:
                            media = client.media_upload(image_path)
                            prev_tweet = client.create_tweet(
                                media_ids=[media.media_id]
                            )
                            prev_tweet_id = prev_tweet.data["id"]
                            os.remove(image_path)
                    elif tweet_text and image_path:
                        media = client.media_upload(image_path)
                        prev_tweet = client.create_tweet(
                            text=tweet_text,
                            media_ids=[media.media_id],
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                        os.remove(image_path)
                    elif tweet_text:
                        prev_tweet = client.create_tweet(
                            text=tweet_text,
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                    elif image_path:
                        media = client.media_upload(image_path)
                        prev_tweet = client.create_tweet(
                            media_ids=[media.media_id],
                            in_reply_to_tweet_id=prev_tweet_id,
                        )
                        prev_tweet_id = prev_tweet.data["id"]
                        os.remove(image_path)
            tweets.pop(time)

with open("tweet.json", "w") as file:
    file.write(json.dumps(tweets))
