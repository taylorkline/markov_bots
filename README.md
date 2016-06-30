Markov Chain Text Generator
===========================

The RandomWriter trains on input text and produces output text that sounds somewhat similar to the input text, with customizable levels of readability. Read in more depth about Markov chains in action at [CodingHorror](https://blog.codinghorror.com/markov-and-you/).

In order to use the text generator, you may import the `RandomWriter` from the `rw` module. Alternatively, you may run `python3 rw.py` to get a helpful description of how to run the application from the commandline.

There is also an example bot included that reads the headlines from various news subreddits and, using the RandomWriter, broadcasts a Tweet that sounds vaguely newslike. See the results [on the FoolishNews Twitter account](https://twitter.com/FoolishNews).

Files
---------------------------
**rw.py**              - The module containing the RandomWriter, which can train on text and output readable 'gibberish'

**rw_tests.py**        - A testing module of the RandomWriter

**graph.py**           - The graph used by the RandomWriter

**example_newsbot.py** - A fully-functional bot that crawls news subreddits for training data and Tweets a gibberish, yet realistic, news headline

**config.ini**         - See below.

config.ini
---------------------------
See the file currently in the repository, as it identifies the tokens required in order to authenticate with Twitter. [Create a Twitter app](https://apps.twitter.com/) in order to obtain these tokens.
