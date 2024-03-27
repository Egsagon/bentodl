'''
    Bentomanga core downloader
    @Egsagon
'''

import os
import time
import zipfile
from playwright.sync_api import sync_playwright
from playwright.sync_api import Route, expect, BrowserContext


def has_url(part: str):
    ''' * '''
    return lambda r: part in r.url

def download_chapter(browser: BrowserContext, url: str, dir: str) -> None:
    ''' * '''
    
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
        ''' * '''
        
        nonlocal current
        
        route.continue_()
        response = route.request.response()
        
        if response:
            raw = response.body()
            
        else:
            print(f'\n\033[91mERROR :: {route.request.url} [{current}/{length}] empty: {route.request.failure}\033[0m')
            return
        
        print(f'\rDownloading [{current}/{length}]', end = '')
        
        with open(dir + str(current) + '.jpeg', 'wb') as file:
            file.write(raw)
        current += 1
        
        if current > length:
            page.goto('about:blank')
        
        time.sleep(.1)
        try:
            page.keyboard.press('ArrowRight')
        except:
            pass # browser can be closed .1s before

    # Start and wait for download completion
    os.makedirs(dir, exist_ok = True)
    
    page.route('**/japanread*.{png,jpg,jpeg}', handle, times = length)
    page.keyboard.press('ArrowRight')
        
    expect(page).to_have_url('about:blank', timeout = 0)
    page.close()
    print()

def download_chapters(urls: list[str], dir: str) -> None:
    ''' * '''
    
    with sync_playwright() as plw:
        # browser = plw.firefox.launch(headless = False)
        browser = plw.firefox.launch_persistent_context(
            user_data_dir = './fox',
            headless = False,
            viewport = {'width': 600, 'height': 400}
        )
        
        for url in urls:
            # Download
            name = url.strip('/').split('/')[-1]
            print('>> Chapter', name)
            download_chapter(browser, url, dir + name + '/')
            
            # Convert to CBZ
            with zipfile.ZipFile(f'{dir}{name}.cbz', 'w') as archive:
                files = os.listdir(dir + name)
                for i, file in enumerate(files):
                    archive.write(f'{dir}{name}/{file}')
                    print(f'\rArchiving [{i + 1}/{len(files)}]', end = '')
                print()
    
    print('Process done.')

if __name__ == '__main__':
    
    root = 'https://bentomanga.com/manga/fire-force/chapter/'
    
    urls = [
        root + str(index)
        for index in range(175, 305)
    ]
    
    download_chapters(urls, './fire-force/')

# EOF