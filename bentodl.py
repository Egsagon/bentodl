'''
Simple CLI for downloader.py
'''

import os
import re
import traceback
import downloader

def ask(prompt: str, default = 'y', ok = 'y') -> bool:
    '''
    Yes/no question
    '''
    
    return ok.lower() in (input(prompt) or default).lower()

re_url = re.compile(r'https://bentomanga\.com/manga/.*?/chapter/.*')

print('\x1b[2m╭─────────────────────────────────────────╮')
print('│\x1b[0m\x1b[96m    https://bentomanga.com downloader    \x1b[0m\x1b[2m│')
print('╰──── Paste chapter URLs, ^C to start ────╯\n')

urls = []

try:
    while 1:
        url = input('\x1b[2m ~ \x1b[0m')
        
        if not re_url.match(url):
            print('\x1B[A\x1b[91m !\x1b[0m')
            continue
        
        print('\x1B[A\x1b[92m +\x1b[0m ')
        urls.append(url)

except KeyboardInterrupt:
    print(f'\n\x1B[A\x1b[2K')

if not urls:
    exit('\x1b[2m<>\x1b[0m \x1b[91mAborted: no valid URL\x1b[0m')


dir = input('\x1b[2m<>\x1b[0m Set output path (default: pwd) ') or './'
if not dir.endswith(('/', '\\')): dir += '/'

headless = ask('\x1b[2m<>\x1b[0m Run headless (requires challenge solver) [y/N] \x1b[0m', 'n')

if headless and not os.path.exists('./fox'):
    if ask('\x1b[2m<>\x1b[93m Installing solver manually is required. Proceed? [Y/n] \x1b[0m'):
        downloader.first_run()

input(f'\x1b[2m<>\x1b[0m Ready to download {len(urls)} chapters. \x1b[2mPress <Enter> to start. \x1b[0m')

try:
    downloader.download_chapters(urls, dir, headless)

except Exception as err:
    
    try:
        print(f'\n\x1b[2m<>\x1b[0m \x1b[91m*** ERROR :: {err.__class__.__name__} - {err} ***')
        input('\x1b[2m<>\x1b[0m \x1b[91m\x1b[2mPress enter to show traceback ')
    except KeyboardInterrupt:
        exit('\x1b[0m')
    
    traceback.print_tb(err.__traceback__)
    print('\x1b[0m\x1b[91m >>>', err, '\x1b[0m')

# EOF