import os
import json
import tweepy
import pendulum

consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret_key = os.environ.get("TWITTER_CONSUMER_SECRET_KEY")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(
    consumer_key=consumer_key, consumer_secret=consumer_secret_key
)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


now = pendulum.now("Asia/Dhaka")
with open("tweet.json") as file:
    tweets = json.load(file)
    for time in list(tweets):
        tweet_time = pendulum.parse(time, tz="Europe/Paris")
        if tweet_time < now:
            if len(tweets[time].keys()) == 1:
                for tweet_text, image_path in tweets[time].items():
                    if tweet_text and image_path:
                        image = api.media_upload(image_path)
                        api.update_status(status=tweet_text, media_ids=[image.media_id])
                        os.remove(image_path)
                    elif tweet_text:
                        api.update_status(status=tweet_text)
                    elif image_path:
                        image = api.media_upload(image_path)
                        api.update_status(status="", media_ids=[image.media_id])
                        os.remove(image_path)

            else:
                prev_tweet = None
                for index, (tweet_text, image_path) in enumerate(tweets[time].items()):
                    if index == 0:

                        if tweet_text and image_path:
                            image = api.media_upload(image_path)
                            prev_tweet = api.update_status(
                                status=tweet_text, media_ids=[image.media_id]
                            )
                            os.remove(image_path)

                        elif tweet_text:
                            prev_tweet = api.update_status(status=tweet_text)

                        elif image_path:
                            image = api.media_upload(image_path)
                            prev_tweet = api.update_status(
                                status="", media_ids=[image.media_id]
                            )
                            os.remove(image_path)

                    elif tweet_text and image_path:
                        image = api.media_upload(image_path)
                        prev_tweet = api.update_status(
                            status=tweet_text,
                            media_ids=[image.media_id],
                            in_reply_to_status_id=prev_tweet.id,
                            auto_populate_reply_metadata=True,
                        )
                        os.remove(image_path)

                    elif tweet_text:
                        prev_tweet = api.update_status(
                            status=tweet_text,
                            in_reply_to_status_id=prev_tweet.id,
                            auto_populate_reply_metadata=True,
                        )

                    elif image_path:
                        image = api.media_upload(image_path)
                        prev_tweet = api.update_status(
                            status="",
                            media_ids=[image.media_id],
                            in_reply_to_status_id=prev_tweet.id,
                            auto_populate_reply_metadata=True,
                        )
                        os.remove(image_path)

            tweets.pop(time)

with open("tweet.json", "w") as file:
    file.write(json.dumps(tweets))
