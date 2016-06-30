from contextlib import contextmanager
import tempfile
import os
import unittest
import itertools
import re
import sys
from pathlib import Path

import rw as randomwriter

@contextmanager
def nonexistant_filename(suffix=""):
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as fi:
        filename = fi.name
    os.remove(filename)
    try:
        yield filename
    finally:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
            
@contextmanager
def filled_filename(content, suffix=""):
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as fi:
        fi.write(content)
        filename = fi.name
    try:
        yield filename
    finally:
        os.remove(filename)

def windowed(iterable, size):
    window = list()
    for v in iterable:
        if len(window) < size:
            window.append(v)
        else:
            window.pop(0)
            window.append(v)
        if len(window) == size:
            yield window

def contains_sequence(iteratable, sequence, length=10000, require_length=True, times=1):
    sequence = list(sequence)
    count = 0
    found = 0
    for window in itertools.islice(windowed(iteratable, len(sequence)), length):
        #print(window, count, sequence)
        count += 1
        if window == sequence:
            found += 1
            if found >= times:
                return True
    #if count < length-1 and require_length:
    #    raise AssertionError("Iterable did not contain enought values for check. Ran out at {}; needed {}.".format(count, length))
    return False


class RandomWriterTests(unittest.TestCase):
    """
    Some simple tests.
    """
    DEFAULT_LENGTH = 10090
    
    def assertContainsSequence(self, iteratable, sequence, length=None, times=1):
        length = length or self.DEFAULT_LENGTH
        lst = list(itertools.islice(iteratable, length + len(sequence)*2))
        if not contains_sequence(lst, sequence, length, times=times):
            self.fail("The given iterable must contain the sequence: {} at least {} times "
                      "(in the first {} elements)\nSample: {}".format(list(sequence), times, length, ", ".join(repr(x) for x in lst[:1000])))
    
    def assertNotContainsSequence(self, iteratable, sequence, length=None):
        length = length or self.DEFAULT_LENGTH
        lst = list(itertools.islice(iteratable, length + len(sequence)*2))
        if contains_sequence(lst, sequence, length):
            self.fail("The given iterable must NOT contain the sequence: {} "
                      "(in the first {} elements)\nSample: {}".format(list(sequence), length, ", ".join(repr(x) for x in lst)))
   
    def test_numeric_sequence(self):
        rw = randomwriter.RandomWriter(2)
        rw.train_iterable((1,2,3,4,5,5,4,3,2,1))
        self.assertContainsSequence(rw.generate(), [3,4,5,5,4,3,2], times=10)
        self.assertNotContainsSequence(rw.generate(), [5,5,3])
        self.assertNotContainsSequence(rw.generate(), [1,2,5])

    def test_words(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.word)
        rw.train_iterable("the given iterable must contain the sequence the")
        self.assertContainsSequence(rw.generate(), "iterable must contain".split(" "), times=10)
        self.assertContainsSequence(rw.generate(), "the sequence".split(" "), times=200)
        self.assertNotContainsSequence(rw.generate(), "the the".split(" "))
        self.assertNotContainsSequence(rw.generate(), "the iterable".split(" "))

    def test_save_load_pickle(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.character)
        rw.train_iterable("abcaea")
        with nonexistant_filename() as fn:
            rw.save_pickle(fn)
            rw2 = randomwriter.RandomWriter.load_pickle(fn)
#             self.assertContainsSequence(rw.generate(), "abc", times=100)
#             self.assertContainsSequence(rw.generate(), "aeaeab", times=100)
#             self.assertNotContainsSequence(rw.generate(), "ac")
#             self.assertNotContainsSequence(rw.generate(), "aa")
#             self.assertNotContainsSequence(rw.generate(), "ce")

    def test_generate_file1(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.character)
        rw.train_iterable("abcaea")
        with nonexistant_filename() as fn:
            rw.generate_file(fn, self.DEFAULT_LENGTH)
            with open(fn, "rt") as fi:
                content = fi.read()
            self.assertContainsSequence(content, "abc", times=100)
            self.assertContainsSequence(content, "aeaeab", times=100)
            self.assertNotContainsSequence(content, "ac")
            self.assertNotContainsSequence(content, "aa")
            self.assertNotContainsSequence(content, "ce")
            
    def test_generate_file_size(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.character)
        rw.train_iterable("abcaea")
        with nonexistant_filename() as fn:
            rw.generate_file(fn, self.DEFAULT_LENGTH)
            with open(fn, "rt") as fi:
                content = fi.read()
            self.assertGreaterEqual(len(content), self.DEFAULT_LENGTH)
            self.assertLessEqual(len(content), self.DEFAULT_LENGTH+2)
            
    def test_generate_file2(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.word)
        rw.train_iterable("a the word the")
        with nonexistant_filename() as fn:
            rw.generate_file(fn, self.DEFAULT_LENGTH)
            with open(fn, "rt") as fi:
                content = fi.read()
            self.assertContainsSequence(content, "the word", times=100)
            self.assertNotContainsSequence(content, "the a")
            
    def test_generate_file3(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.none)
        rw.train_iterable((1,2,3,4,5,5,4,3,2,1))
        with nonexistant_filename() as fn:
            rw.generate_file(fn, self.DEFAULT_LENGTH)
            with open(fn, "rt") as fi:
                content = fi.read()
            self.assertContainsSequence(content, "3 4 5 5 4 3 2", times=100)
            self.assertNotContainsSequence(content, "5 5 3")
            self.assertNotContainsSequence(content, "1 2 5")
            
    def test_generate_file_bytes(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.byte)
        rw.train_iterable(b"What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          b"in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        with nonexistant_filename() as fn:
            rw.generate_file(fn, self.DEFAULT_LENGTH)
            with open(fn, "rt") as fi:
                content = fi.read()
            self.assertContainsSequence(content, "worm")
            
    def test_numeric_sequence_in(self):
        rw = randomwriter.RandomWriter(2)
        rw.train_iterable((1,2,3,4,5,5,5,4,3,2,1,2,4,5))
        self.assertIsInstance(next(iter(rw.generate())), int)
        self.assertContainsSequence(rw.generate(), [3,4,5,5,4,3,2], times=10)
        self.assertContainsSequence(rw.generate(), [3,4,5,5,5,5,4,3,2])
        self.assertContainsSequence(rw.generate(), [5,5,5,5,5])
        self.assertContainsSequence(rw.generate(), [3,2,1,2,4,5,5,4])
        self.assertContainsSequence(rw.generate(), [3,2,1,2,3,4,5,5,4])

    def test_numeric_sequence_notin(self):
        rw = randomwriter.RandomWriter(2)
        rw.train_iterable((1,2,3,4,5,5,5,4,3,2,1,2,4,5))
        self.assertNotContainsSequence(rw.generate(), [5,5,3])
        self.assertNotContainsSequence(rw.generate(), [1,2,5])
        self.assertNotContainsSequence(rw.generate(), [4,2])
        self.assertNotContainsSequence(rw.generate(), ["5"])

    def test_generate_count(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.character)
        rw.train_iterable("What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          "in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        generated = len(list(itertools.islice(rw.generate(), 10000)))
        self.assertEqual(generated, 10000)

    def test_characters(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.character)
        rw.train_iterable("What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          "in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        self.assertIsInstance(next(iter(rw.generate())), str)
        self.assertContainsSequence(rw.generate(), "worm")
        self.assertNotContainsSequence(rw.generate(), "mals ")

    def test_characters_level3(self):
        rw = randomwriter.RandomWriter(3, randomwriter.Tokenization.character)
        rw.train_iterable("What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          "in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        self.assertIsInstance(next(iter(rw.generate())), str)
        self.assertContainsSequence(rw.generate(), "n how n")
        self.assertNotContainsSequence(rw.generate(), "worm")
        self.assertNotContainsSequence(rw.generate(), "mals ")

    def test_bytes(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.byte)
        rw.train_iterable(b"What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          b"in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        self.assertTrue(isinstance(next(iter(rw.generate())), (int, bytes)))
        self.assertContainsSequence(rw.generate(), b"worm")
        self.assertNotContainsSequence(rw.generate(), b"mals ")

    def test_words2(self):
        rw = randomwriter.RandomWriter(2, randomwriter.Tokenization.word)
        rw.train_iterable("What a piece of work is man! how noble in reason! how infinite in faculty! in form and moving how express and admirable! "
                          "in action how like an angel! in apprehension how like a god! the beauty of the world, the paragon of animals!")
        self.assertIsInstance(next(iter(rw.generate())), str)
        self.assertContainsSequence(rw.generate(), "action how like a god!".split(" "), length=50000)
        self.assertContainsSequence(rw.generate(), "infinite in faculty!".split(" "), length=50000)
        self.assertNotContainsSequence(rw.generate(), "man angel".split(" "), length=50000)
        self.assertNotContainsSequence(rw.generate(), "infinite in reason".split(" "), length=50000)
        self.assertNotContainsSequence(rw.generate(), ("worm",))

    def test_train_url_characters(self):
        rw = randomwriter.RandomWriter(3, randomwriter.Tokenization.character)
        rw.train_url("https://www.gutenberg.org/cache/epub/24132/pg24132.txt")
        self.assertContainsSequence(rw.generate(), "ad di", length=200000)
            
    def test_train_url_bytes(self):
        rw = randomwriter.RandomWriter(4, randomwriter.Tokenization.byte)
        rw.train_url("https://www.gutenberg.org/cache/epub/24132/pg24132.txt")
        self.assertContainsSequence(rw.generate(), b"ad di", length=300000)

    def test_train_url_word(self):
        rw = randomwriter.RandomWriter(1, randomwriter.Tokenization.word)
        rw.train_url("https://www.gutenberg.org/cache/epub/24132/pg24132.txt")
        self.assertContainsSequence(rw.generate(), "she had".split(), length=100000)

    def test_train_url_utf8(self):
        rw = randomwriter.RandomWriter(5, randomwriter.Tokenization.character)
        rw.train_url("http://www.singingwizard.org/stuff/utf8test.txt")
        self.assertContainsSequence(rw.generate(), "ajtób", length=100000)


if __name__ == "__main__":
    unittest.main()
