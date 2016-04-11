# Reading dotEnv file
import os
config = {}
fileDir = os.path.dirname(os.path.realpath('__file__'))
with open(os.path.join(fileDir, '.env'), 'r') as f:
    for line in f:
        line = line.rstrip() #removes trailing whitespace and '\n' chars

        if "=" not in line: continue #skips blanks and comments w/o =
        if line.startswith("#"): continue #skips comments which contain =

        k, v = line.split("=", 1)
        config[k] = v

from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from footprintsbot.items import Issue
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors import LinkExtractor
from datetime import datetime
import json
import re

USERNAME=config['USERNAME']
PASSWORD=config['PASSWORD']
TICKET_URL_PATTERN=config['TICKET_URL_PATTERN']
PAGE_RE = re.compile('([0-9]+),,[0-9]*,.*')

class FootprintsSpider(InitSpider):
    name = "footprints"
    allowed_domains = ["servicedesk.niwa.co.nz"]
    login_page = config['CONFIG_URL']
    start_urls = [
        config['START_URL_PATTERN'] % (USERNAME, USERNAME)
    ]

    rules = (
        #requires trailing comma to force iterable vs tuple
        Rule(LinkExtractor(), callback='parse_item', follow=True),

    )

    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        return FormRequest.from_response(response,
                    formdata={'USER': USERNAME, 'PASSWORD': PASSWORD, 'REMEMBER_PASSWORD': '', 'PROJECTID': '-1', 'SCREEN': '1'},
                    callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        if "FormRedirect()" in response.body:
            self.log("Successfully logged in. Let's start crawling!")
            # Now the crawling can begin..
            self.initialized()
            for url in self.start_urls:
                # Result of these requests will be in parse function
                yield self.make_requests_from_url(url)
        else:
            self.log(response.body)
            self.log("Error logging in :(")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        """Parse items in the main page of Footprints. When there is pagination,
        you simply yield another request to the next page using this same function
        as callback."""
        self.log('Parsing main page')
        body = response.body_as_unicode()
        index1 = body.index('var ticketData = {')
        if index1 > 0:
            temp = ']};'
            index2 = body.index(temp , index1+1)

            if index2 > 0:
                text = body[index1+len('var ticketData = '):index2+len(temp)-1]

                #self.log(text)
                j = json.loads(text)
                rows = j['rows']

                for row in rows:
                    rowId = row['rowId']
                    ticketId = rowId[:rowId.index('_')]

                    url = TICKET_URL_PATTERN % (USERNAME, USERNAME, ticketId)
                    #self.log(url)
                    # yield a request to this URL, with another function to parse the Issue body
                    yield Request(url, callback=self.parse_item)
                    # NOTE: when testing, UNcomment the following line to index a single ticket
                    #break

                has_next_page = 'javascript:document.nextpage.submit()' in body

                if has_next_page:
                    links = response.xpath("//input[@name='MAXMININC'][1]/@value").extract()
                    a_link = links[0].strip()
                    other_link = links[1].strip()

                    MAXMININC = ''
                    if a_link == '':
                        MAXMININC = other_link
                    elif other_link == '':
                        MAXMININC = a_link
                    else:
                        a_m = PAGE_RE.match(a_link)
                        other_m = PAGE_RE.match(other_link)

                        if a_m and other_m:
                            a_number = a_m.group(1)
                            other_number = other_m.group(1)

                            if a_number > other_number:
                                MAXMININC = a_link
                            else:
                                MAXMININC = other_link

                    self.log('Next page is: %s' % MAXMININC)
                    if MAXMININC != '':
                        # From: http://stackoverflow.com/questions/30342243/send-post-request-in-scrapy
                        frmdata = {"USER": USERNAME, "PROJECTID": "1", "MRP": "", "CUTM": USERNAME, "SOLSEARCH": "", "SOLUTIONS_FROM_OTHER_PROJ": "", "KB": "", "SAVEDNAME": "", "VIEWTOTAL": "", "PROJECT_TOTALS_STATUS": "", "MAINFRAMEONLY": "1", "LASTMR": "", "FROM SELECTCONTACT": "0", "WRITECACHE": "1", "KBONLY": "", "INTERNALKB": "", "SEARCHS": "", "SEARCH_KB_CONTROLS": "0", "KEEP_DIRTY_CONTROLS": "0", "KEEP_DIRTY_FILTER": "1", "VIEWMYREQ": "1", "CUSTM": USERNAME, "MAXMININC": MAXMININC}
                        url = config['PAGINATION_URL']
                        # NOTE: When testing, COmment out this line to index a single page...
                        yield FormRequest(url, callback=self.parse, formdata=frmdata, dont_filter=True)

    def parse_item(self, response):
        """
        Parse a ticket page. Extracting issue information, and returning the element to be serialised.
        """
        self.log('Parsing issue page...')
        body = response.body

        issue = Issue()
        
        dialogue_title = response.xpath("//td[@class='dialogTitle']/text()").extract()[0]
        issue['id'] = dialogue_title.split(' ')[1]

        issue['first_name'] = response.xpath("//input[@name='First__bName'][1]/@value").extract()[0]
        issue['last_name'] = response.xpath("//input[@name='Last__bName'][1]/@value").extract()[0]

        issue['status'] = response.xpath("//div[@id='statCell']/text()").extract()[0].strip()
        issue['issuetype'] = 'N/A'
        issue['status2'] = 'N/A'
        issue['description'] = response.xpath("//div[@id='SHORTD']/text()").extract()[0].strip()

        messages = response.xpath("//div[@class='descShowAll']")
        count_messages = len(messages)
        issue['interactions'] = count_messages

        first_message_id = 'descGen_1'
        last_message_id  = 'descGen_' + str(count_messages)
        created_value = None
        last_updated_value = None
        parties = []
        for message in messages:
            description_timestamp = message.xpath('div[@class="descriptionTimestamp"]/text()').extract()[0]
            party_name_index = description_timestamp.index('00) by ') + len('00) by ')
            party = description_timestamp[party_name_index:-1].strip()
            parties.append(party)
            if message.xpath('@id').extract()[0] == first_message_id:
                ifrom = len('Entered on ')
                ito = ifrom + len('00/00/0000 at 00:00:00')
                created = description_timestamp[ifrom:ito]
                created = created.replace(' at ', ' ')
                created_datetime = datetime.strptime(created, '%d/%m/%Y %H:%M:%S')
                created_value = created_datetime
                issue['created'] = created_value.strftime("%Y-%m-%dT%H:%M:%S")

            if message.xpath('@id').extract()[0] == last_message_id:
                ifrom = len('Entered on ')
                ito = ifrom + len('00/00/0000 at 00:00:00')
                last_updated = description_timestamp[ifrom:ito]
                last_updated = last_updated.replace(' at ', ' ')
                last_updated_datetime = datetime.strptime(last_updated, '%d/%m/%Y %H:%M:%S')
                last_updated_value = last_updated_datetime
                issue['last_updated'] = last_updated_value.strftime("%Y-%m-%dT%H:%M:%S")

        issue['parties'] = '|'.join(parties)
        if created_value is not None and last_updated_value is not None:
            issue['created_updated_diff'] = (last_updated_value - created_value).total_seconds()

        yield issue
