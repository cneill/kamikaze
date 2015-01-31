#!/usr/bin/env python
"""
Kamikaze!

Usage:
    kamikaze.py list (path|headers) [--procs=INT] [--multidir] [--ignore=STATUS_CODE]... WORDLIST TARGET ...
    kamikaze.py brute (path|headers) [--procs=INT] [--charset=STRING] [--min_len=INT] [--max_len=INT] [--multidir] [--ignore=STATUS_CODE]... TARGET ...

Options:
    list                     Search with a wordlist
    brute                    Search by generating permutations of all characters in the range
        --charset=STRING     A string of characters to use in the search [default: abcdefghijklmnopqrstuvwxyz]
        --min_len=INT        Specify the maximum length of a generated word [default: 6]
        --max_len=INT        Specify the minimum length of a generated word [default: 1]
    path                     Send strings to the URL
    headers                  Send strings to each of the header fields
    --procs=INT              Number of worker processes to spawn [default: 10]
    --multidir               Go multiple directories deep
    --ignore=STATUS_CODE     Status codes to ignore
"""
from docopt import docopt
import requests

import sys
import string
import os.path
import itertools
import signal
from multiprocessing import Pool, Value
from functools import partial


counter = Value('i', 0)
total = Value('i', 0)


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


# Handle output to the console
def write(string, complete=False, sub=0, sep=False, raw=False,
          verbosity=True, error=False):
    status = '-'
    if complete:
        status = '+'
    if error:
        status = '!'

    # print substatements only if verbosity > 0
    if verbosity:
        if raw:
            sys.stdout.write(string)
        elif sub:
            sys.stdout.write(' [{0}]{1}=> {2}\n'.format(status, ('  ' * sub),
                             string))
        elif sep:
            sys.stdout.write('=' * 80)

    if not sep and not sub and not raw:
        sys.stdout.write(' [' + status + '] ' + string + '\n')

    sys.stdout.flush()


def read_wordlist(wordlist):
    write('Reading search wordlist...')
    contents = []
    if os.path.isfile(wordlist):
        with open(wordlist, 'r') as f:
            for line in f:
                if line.strip():
                    contents.append(line.strip())
    else:
        write("Couldn't find wordlist", error=True)
    return contents


def generate_wordlist(charset=string.ascii_lowercase, min_length=1,
                      max_length=6):
    write('Generating search wordlist...')
    if type(charset) is not str:
        write('Invalid charset', error=True)

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
    global counter, total
    progress = float(counter.value) / total
    status = " [-] Processed {0}/{1} requests [{2:.2%}]".format(counter.value,
                                                                total,
                                                                progress)
    status += (chr(8) * (len(status) * 3))

    write(status, raw=True, sub=True)

    path = '/'.join(url.split('/')[2:])
    try:
        resp = requests.get(url)
        with counter.get_lock():
            counter.value += 1
        if resp.status_code not in ignore:
            write('Status code ({0}) at {1}'.format(
                resp.status_code, path), sub=1)
            write('Body snippet:\n{0}'.format(resp.text[:500]), sub=2)

    except requests.exceptions.ConnectionError, e:
        write('Connection error: {0}'.format(e), error=True)

    except (KeyboardInterrupt, SystemExit):
        write('Exiting...', raw=True)
        sys.exit()


def path_search(targets, wordlist=None, multidir=False, ignore=None, procs=80):
    global total
    if not wordlist:
        write('Must include wordlist', error=True)
        return None

    for target in targets:
        write('Beginning path search on target {0}'.format(target))
        urls = []
        for word in wordlist:
            url = '{0}{1}'.format(target, word)
            urls.append(url)

        if multidir:
            for word in wordlist:
                for word2 in wordlist:
                    url = '{0}{1}/{2}'.format(target, word, word2)
                    urls.append(url)

        total = len(urls)
        p = Pool(processes=procs, initializer=init_worker)
        mfunc = partial(url_get, ignore=ignore)
        try:
            p.map_async(mfunc, urls).get(9999)
        except (KeyboardInterrupt, SystemExit):
            write('Exiting...', raw=True)
            sys.exit()

    write('\n', raw=True)
    write('Search complete!', complete=True)


def header_search(targets, wordlist=None):
    print 'ha'


def main(args):
    wordlist = None
    multidir = False
    targets = []
    ignore = [404]
    procs = 80

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
        write('Must choose either wordlist or brute force mode', error=True)

    if args['--procs']:
        procs = int(args['--procs'])

    if args['--multidir']:
        multidir = True

    if args['TARGET']:
        targets = process_targets(args['TARGET'])
    else:
        write('Must include a target', error=True)

    if args['--ignore']:
        ignore = map(int, args['--ignore'])

    if args['path']:
        kwds = {'wordlist': wordlist,
                'multidir': multidir,
                'ignore': ignore,
                'procs': procs}
        path_search(targets, **kwds)

    elif args['headers']:
        header_search(targets, wordlist=wordlist, multidir=multidir,
                      ignore=ignore)
    else:
        write('Unknown command', error=True)

if __name__ == '__main__':
    args = docopt(__doc__, version='0.0')

    try:
        main(args)
    except (KeyboardInterrupt, SystemExit):
        write('\nExiting...', raw=True)
        sys.exit()
