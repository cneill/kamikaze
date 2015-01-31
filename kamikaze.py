#!/usr/bin/env python
"""
Kamikaze!
Usage:
    kamikaze.py list (path|headers) [--multidir] [--ignore=STATUS_CODE]... WORDLIST TARGET ...
    kamikaze.py brute (path|headers) [--charset=STRING] [--min_len=INT] [--max_len=INT] [--multidir] [--ignore=STATUS_CODE]... TARGET ...

Options:
    list                     Attack with a wordlist
    brute                    Attack by generating permutations of all characters in the range
        --charset=STRING     A string of characters to use in the attack [default: abcdefghijklmnopqrstuvwxyz]
        --min_len=INT     Specify the maximum length of a generated word [default: 6]
        --max_len=INT     Specify the minimum length of a generated word [default: 1]
    path                     Send strings to the URL
    headers                  Send strings to each of the header fields
    --multidir               Go multiple directories deep
    --ignore=STATUS_CODE     Status codes to ignore
"""
from docopt import docopt
import requests

import string
import os.path
import itertools
from multiprocessing import Pool
from functools import partial


def read_wordlist(wordlist):
    contents = []
    if os.path.isfile(wordlist):
        with open(wordlist, 'r') as f:
            for line in f:
                contents.append(line.strip())
    else:
        print "Couldn't find wordlist"
    return contents


def generate_wordlist(charset=string.ascii_lowercase, min_length=1,
                      max_length=6):
    print 'Generating attack wordlist...'
    if type(charset) is not str:
        print 'invalid charset'

    wordlist = []

    for i in xrange(min_length, max_length+1):
        for line in itertools.product(charset, repeat=i):
            wordlist.append(''.join(line))

    return wordlist


def process_targets(targets):
    result_targets = []

    if type(targets) is string:
        targets = [targets]

    for target in targets:
        if not target.startswith('http://'):
            pass
        result_targets.append(target)

    return result_targets


def url_get(url, ignore=[]):
    path = '/' + '/'.join(url.split('/')[1:])
    try:
        resp = requests.get(url)
        if resp.status_code not in ignore:
            print 'Status code ({0}) at {1}'.format(
                resp.status_code, path)
            print '\tBody snippet:\n{0}'.format(resp.text[:500])

    except requests.exceptions.ConnectionError, e:
        print 'Connection error: ', e


def path_attack(targets, wordlist=None, multidir=False, ignore=None):
    if not wordlist:
        print 'Must include wordlist'
        return None

    for target in targets:
        print 'Beginning path attack on target {0}'.format(target)
        urls = []
        for word in wordlist:
            url = '{0}{1}'.format(target, word)
            urls.append(url)

        p = Pool(processes=100)
        mfunc = partial(url_get, ignore=ignore)
        p.map(mfunc, urls)


def header_attack(targets, wordlist=None):
    print 'ha'


def main(args):
    wordlist = None
    multidir = False
    targets = []
    ignore = [404]

    if args['list']:
        wordlist = read_wordlist(args['WORDLIST'])

    elif args['brute']:
        charset = None
        max_length = None

        if args['--charset']:
            charset = args['--charset']
        if args['--min_len']:
            min_length = int(args['--min_len'])
        if args['--max_len']:
            max_length = int(args['--max_len'])

        wordlist = generate_wordlist(charset=charset, min_length=min_length,
                                     max_length=max_length)

    else:
        print 'Must choose either wordlist or brute force mode'

    if args['--multidir']:
        multidir = True

    if args['TARGET']:
        targets = process_targets(args['TARGET'])
    else:
        print 'Must include a target'

    if args['--ignore']:
        ignore = map(int, args['--ignore'])

    if args['path']:
        kwds = {'wordlist': wordlist,
                'multidir': multidir,
                'ignore': ignore}
        path_attack(targets, **kwds)

    elif args['headers']:
        header_attack(targets, wordlist=wordlist, multidir=multidir,
                      ignore=ignore)
    else:
        print 'Unknown command'

if __name__ == '__main__':
    args = docopt(__doc__, version='0.0')
    try:
        main(args)
    except KeyboardInterrupt:
        print 'Exiting...'
