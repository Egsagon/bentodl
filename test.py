import re
import string
from playwright.sync_api import sync_playwright, Request, Route, expect

ROOT = 'https://bentomanga.com'

def is_api_call(type_: str) -> object:
    def wrap(request: Request):
        return request.url.startswith(ROOT + '/api/') \
            and type_ in request.url
    return wrap

def is_image(url: str) -> object:
    def wrap(request: Request):
        return request.resource_type == 'image' and url in request.url
    return wrap

IID = 0
def downloader(route: Route) -> object:
    global IID
    print('| DL |', route.request.url,'::', IID)
    route.continue_()
    
    raw = route.request.response().body()
    with open(str(IID) + '.jpeg', 'wb') as file:
        file.write(raw)
    IID += 1

if __name__ == '__main__':
    
    url = 'https://bentomanga.com/manga/undead-unluck-colored-edition-fr/'
    
    with sync_playwright() as plw:
        
        browser = plw.firefox.launch(headless = False)
        context = browser.new_context()
        
        # context.route('**', lambda r: r.continue_()) # disable http cache        
        page = context.new_page()
        
        # Get manga ID
        page.goto(url, wait_until = 'networkidle')
        page.wait_for_selector('.component-stats', timeout = 0)
        manga_id = page.query_selector('.component-stats').get_attribute('data-manga')
        print('>> Found ID:', manga_id)
        
        # Get manga tree
        page.goto(url + 'chapter/61', wait_until = 'commit') # TODO
        with page.expect_request_finished(is_api_call('=manga'), timeout = 0) as event:
            tree = event.value.response().json()
        
        # Print chapters
        # print('>> Found manga:', tree['manga']['title'])
        # for chapter_id, chapter in tree['chapter'].items():
        #     print(f' - Volume {chapter["volume"]} chapter {chapter["chapter"]} :: "{chapter["title"]}"')
        
        # Download each chapter
        for chapter in tree['chapter'].values():
            
            # Load page
            chapter_slug = chapter['chapter']
            assert chapter_slug # TODO support HS
            
            page.goto(url + 'chapter/' + chapter_slug, wait_until = 'commit', timeout = 0)
            
            with page.expect_request_finished(is_api_call('=chapter'), timeout = 0) as event:
                chapter_data = event.value.response().json()
            
            chapter_length = len(chapter_data['page_array'])
            print('Awaiting', chapter_length)

            page.route('**/*.{jpeg}', downloader)
            
            # Press right arrow key
            for image in chapter_data['page_array']:
                page.expect_request_finished(is_image(image))
                page.keyboard.press('ArrowRight')
            
            # We will scroll until next redirect
            expect(page).to_have_url(re.compile(f'^(?!{page.url})'), timeout = 0)
            page.wait_for_timeout(1000)

# EOF