'''
    Bentomanga core downloader
'''

import os
import time
import zipfile
from playwright.sync_api import sync_playwright
from playwright.sync_api import Route, expect, BrowserContext, Playwright

# Noptcha is used to automatically solve cloudflare challenges.
# Free plan has a rate limit of ~100/day. If you want to do more
# Solve challenges manually or use VPN + reset browser each time
EXT_URL = 'https://addons.mozilla.org/fr/firefox/addon/noptcha/'

def has_url(part: str):
    ''' * '''
    
    return lambda r: part in r.url

def download_chapter(browser: BrowserContext, url: str, dir: str) -> None:
    '''
    Download all images from a single chapter to a directory.
    '''
    
    # Open URL and wait until response received to catch all requests
    # Using multiple pages and close them rather than a single page
    # for performance
    page = browser.new_page()
    page.goto(url, wait_until = 'commit', timeout = 0)
    
    # Disable chaching
    page.route('**/*', lambda r: r.continue_())
    
    # Wait for data request
    with page.expect_request_finished(predicate = has_url('type=chapter'),
                                      timeout = 0) as event:
        data = event.value.response().json()
    
    # Setup downloader
    length = len(data['page_array'])
    current = 1
    
    def handle(route: Route):
        '''
        Called with each image request received.
        '''
        
        nonlocal current
        
        # Approve request
        route.continue_()
        response = route.request.response()
        
        # Make sure request did not raise NS_BINDING_ERROR (prob CF timeout)
        if response:
            raw = response.body()
        
        else:
            print(f'\n\033[91mERROR :: {route.request.url} [{current}/{length}] empty: {route.request.failure}\033[0m')
            return

        print(f'\r\x1b[2m<> Downloading [\x1b[0m{current}\x1b[2m/\x1b[0m{length}\x1b[2m] \x1b[0m', end = '')
        
        # Download image
        with open(dir + str(current) + '.jpeg', 'wb') as file:
            file.write(raw)
        current += 1
        
        # Leave page if download finished
        if current > length:
            page.goto('about:blank')
        
        # Scroll to next page
        # Delay can be tuned, should remain above CF timeout
        time.sleep(.1)
        try: page.keyboard.press('ArrowRight')
        except: pass # browser can be closed .1s before

    # Start and wait for download completion
    os.makedirs(dir, exist_ok = True)
    
    # Route all CDN requests to the handle
    page.route('**/japanread*.{png,jpg,jpeg}', handle, times = length)
    page.keyboard.press('ArrowRight')
    
    # Wait until page is left and close it
    expect(page).to_have_url('about:blank', timeout = 0)
    page.close()

def start(plw: Playwright, viewport: dict = None, headless: bool = False) -> BrowserContext:
    '''
    Start a browser instance.
    Using a persistent context for extension support, but a normal one can be used
    when not using headless mode.
    '''
    
    print('\x1b[2m<> Starting browser\x1b[0m')
    return plw.firefox.launch_persistent_context(
        user_data_dir = './fox',
        headless = headless,
        viewport = viewport or {'width': 600, 'height': 400}
    )

def first_run() -> None:
    '''
    Open a browser instance for noptcha to be installed manually.
    See https://github.com/microsoft/playwright/issues/7297
    '''
    
    with sync_playwright() as plw:
        browser = start(plw, viewport = {'width': 1200, 'height': 600}, headless = False)
        
        # Use the first context page so use has only one page to close
        page = browser.pages[0]
        page.goto(EXT_URL)
        
        # Wait for user to close browser
        browser.wait_for_event('close')

def download_chapters(urls: list[str], dir: str, headless: bool = False) -> None:
    '''
    Download a list of chapters using the same browse.
    '''
    
    with sync_playwright() as plw:
        browser = start(plw, headless = headless)
        
        for url in urls:
            # Get name
            name = url.strip('/').split('/')[-1]
            width = os.get_terminal_size().columns
            print('\x1b[2m<> Loading...\x1b[0m' + (f'Chapter {name} << ').rjust(width - 14), end = '')
            
            # Download
            download_chapter(browser, url, dir + name + '/')
            
            # Convert to CBZ
            with zipfile.ZipFile(f'{dir}{name}.cbz', 'w') as archive:
                files = os.listdir(dir + name)
                for i, file in enumerate(files):
                    archive.write(f'{dir}{name}/{file}')
                    print(f'\r\x1b[2m<> Archiving   [\x1b[0m{i + 1}\x1b[2m/\x1b[0m{len(files)}\x1b[2m] \x1b[0m', end = '')
                print()
    
    print('\n\x1b[2m<>\x1b[0m\x1b[92m Process finished successfully.\x1b[0m')

# EOF