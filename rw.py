from enum import Enum
import urllib.request
import graph
import pickle
import argparse
import sys
import tempfile


class Tokenization(Enum):
    """
    word: Interpret the input as UTF-8 and split the input at any
      white-space characters and use the strings between the white-space
      as tokens. So "a b" would be ["a", "b"] as would "a\n b".

    character: Interpret the input as UTF-8 and use the characters as
      tokens.

    byte: Read the input as raw bytes and use individual bytes as the
      tokens.

    none: Do not tokenize. The input must be an iterable.
    """
    word = 1
    character = 2
    byte = 3
    none = 4


class RandomWriter(object):
    """
    A Markov chain based random data generator.
    """

    def __init__(self, level, tokenization=Tokenization.none):
        """
        Initialize a random writer.

        Args:
          level: The context length or "level" of model to build.
          tokenization: A value from Tokenization. This specifies how
            the data should be tokenized.

        The value given for tokenization will affect what types of
        data are supported.
        """
        if level < 0:
            raise ValueError("The level of analysis must be >= 0.")
        if tokenization not in Tokenization:
            raise ValueError("You did not provide a valid tokenization mode.")

        self._mode = tokenization
        self._level = level
        self._graph = None

    def generate(self):
        """
        Yield random tokens using the model, infinitely.
        """
        if self._graph is None:
            raise ValueError("The RandomWriter must be trained before it can"
                             "generate tokens.")

        while True:
            yield self._graph.get_random_token()

    def generate_file(self, filename, amount):
        """
        Write a file using the model.

        Args:
          filename: The name of the file to write output to.
          amount: The number of tokens to write.

        For character or byte tokens this will just output the
        tokens one after another. For any other type of token a space
        will be added between tokens.
        """
        if self._mode is Tokenization.byte:
            if not hasattr(filename, 'write'):
                with open(filename, mode="wb") as fi:
                    self.generate_file(fi, amount)
            else:
                gen = self.generate()
                filename.write(bytes(next(gen) for _ in range(amount)))
        else:
            if not hasattr(filename, 'write'):
                with open(filename, mode="w", encoding="utf-8") as fi:
                    self.generate_file(fi, amount)
            else:
                for _ in range(amount):
                    content = str(next(self.generate()))
                    if self._mode is not Tokenization.character:
                        content += " "

                    filename.write(content)

    def save_pickle(self, filename_or_file_object):
        """
        Write this model out as a Python pickle.

        Args:
          filename_or_file_object: A filename or file object to write to.

        File objects assumed to be opened in binary mode.
        """
        if hasattr(filename_or_file_object, 'write'):
            pickle.dump(self, filename_or_file_object, pickle.HIGHEST_PROTOCOL)
        else:
            # Better open the file first
            with open(filename_or_file_object, "wb") as fi:
                self.save_pickle(fi)

    @classmethod
    def load_pickle(cls, filename_or_file_object):
        """
        Loads a Python pickle and make sure it is in fact a model.

        Args:
          filename_or_file_object: A filename or file object to load
            from.
        Return:
          A new instance of RandomWriter which contains the loaded
          data.

        File objects assumed to be opened in binary mode.
        """
        try:
            data = pickle.load(filename_or_file_object)
            if isinstance(data, cls):
                return data
            else:
                # Something bad happened
                raise ValueError("A RandomWriter could not be loaded from the"
                                 "file.")
        except TypeError:
            # Better open the file first
            with open(filename_or_file_object, "rb") as fi:
                data = pickle.load(fi)
                return data

    def train_url(self, url):
        """
        Compute the probabilities based on the data downloaded from url.

        Args:
          url: The URL to download.

        """
        if self._mode is Tokenization.none:
            raise ValueError("This method is only supported if the "
                             " tokenization mode is not none.")

        with urllib.request.urlopen(url) as response:
            text = response.read()

        if self._mode is not Tokenization.byte:
            try:
                text = str(text, encoding="utf-8")
            except UnicodeDecodeError:
                # Can't decode as UTF-8, so just try our best
                text = str(text)

        self.train_iterable(text)

    def train_iterable(self, data):
        """
        Compute the probabilities based on the data given.

        If the tokenization mode is none, data must be an iterable. If
        the tokenization mode is character or word, then data must be
        a string. Finally, if the tokenization mode is byte, then data
        must be a bytes. If the type is wrong, TypeError raised.
        """
        data = self.validate_datatype(data)
        if data is None:
            raise TypeError("Incorrect data given for tokenization mode.")

        self._graph = graph.Graph()
        if self._level is 0:
            for i in range(len(data)):
                state = tuple(data[i:i+1])
                self._graph.add_edge(state)
        else:
            for i in range(len(data) - self._level + 1):
                # get a slice of self._level tokens to store in the graph
                state = tuple(data[i:i+self._level])

                self._graph.add_edge(state)

    def validate_datatype(self, data):
        """
        Ensures the validity of the given data type with the Tokenization mode,
        returning data in the correct form for future iteration or None if
        invalid combination of data and mode.
        """
        if self._mode is Tokenization.word and isinstance(data, str):
            return data.split()
        elif (self._mode is Tokenization.character and isinstance(data, str) or
              self._mode is Tokenization.byte and isinstance(data, bytes) or
              self._mode is Tokenization.none and hasattr(data, '__iter__')):
            return data
        else:
            return None


def train_input(args):
    """
    Constructs a RandomWriter using the given level and tokenization.

    Then trains on the input file or stdin.

    Finally, it pickles itself to the output file or stdout.
    """
    if args.character:
        tokenization = Tokenization.character
    elif args.byte:
        tokenization = Tokenization.byte
    else:
        tokenization = Tokenization.word

    rw = RandomWriter(args.level, tokenization)

    if args.input is sys.stdin:
        data = args.input.read()
        rw.train_iterable(data)
    else:
        rw.train_url(args.input)

    rw.save_pickle(args.output)


def generate_output(args):
    """
    Constructs a RandomWriter from a pickle and proceeds to output the
    given amount of generated tokens.
    """
    rw = RandomWriter.load_pickle(args.input)

    rw.generate_file(args.output, args.amount)

if __name__ == '__main__':
    """
    Handles parsing of command line arguments.
    """
    parser = argparse.ArgumentParser(add_help=True)
    subparsers = parser.add_subparsers()

    # The train argument
    parser_train = subparsers.add_parser('train', help="Train a model given "
                                         "input and save to pickle output.")
    parser_train.add_argument('--input', default=sys.stdin)
    parser_train.add_argument('--output', default=sys.stdout.buffer)

    token_group = parser_train.add_mutually_exclusive_group()
    token_group.add_argument('--word', action='store_true')
    token_group.add_argument('--character', action='store_true')
    token_group.add_argument('--byte', action='store_true')

    parser_train.add_argument('--level', type=int, default=1)
    parser_train.set_defaults(func=train_input)

    # The generate argument
    parser_generate = subparsers.add_parser('generate', help="Generate an "
                                            "output file.")
    parser_generate.add_argument('--input', default=sys.stdin.buffer)
    parser_generate.add_argument('--output', default=sys.stdout)
    parser_generate.add_argument('--amount', required=True, type=int)
    parser_generate.set_defaults(func=generate_output)

    # because we are only using subparsers, argparse will not print help
    # by default, so do it manually.
    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()
    args.func(args)
