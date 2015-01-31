# Kamikaze

## Usage

`
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
`
