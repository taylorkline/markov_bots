from rw import RandomWriter
from rw import Tokenization
from configparser import ConfigParser
import praw
import tweepy

reddit_agent = "praw:generatenews:v1.0 (by nobody)"
subreddits = ["news", "worldnews", "upliftingnews"]
limit = 1000
analysis_level = 12
tokenization = Tokenization.character
char_limit = 140

# Authenticate with Twitter
config = ConfigParser()
with open("config.ini") as cfgfile:
    config.read_file(cfgfile)
twitter_cfg = config["twitter"]
auth = tweepy.OAuthHandler(twitter_cfg["consumer_key"], twitter_cfg["consumer_secret"])
auth.set_access_token(twitter_cfg["access_token"], twitter_cfg["access_secret"])
t = tweepy.API(auth)

# Access Reddit API
r = praw.Reddit(reddit_agent)

titles = ""
for subreddit in subreddits:
    """
    Aggregate the titles for processing.
    """
    hot = r.get_subreddit(subreddit).get_hot(limit=limit)
    for thread in hot:
        titles += thread.title + " "

rw = RandomWriter(analysis_level, tokenization)
rw.train_iterable(titles)

tweet = ""
for _ in range(char_limit):
    tweet += next(rw.generate())
tweet += "."

# Drop the first characters before any whitespace to look more authentic
tweet = tweet.partition(' ')[2]

# Capitalize the first letter, without changing the rest.
tweet = tweet[0].capitalize() + tweet[1:]

t.update_status(tweet)
print("{} just tweeted: {}".format(t.me().screen_name, tweet))
