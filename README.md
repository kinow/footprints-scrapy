# FootPrints scraper

This scraper uses [Scrapy](http://scrapy.org/). The easiest way to install it is
with Anaconda, choosing Python 2, and installing it with the conda utility.

## Running the crawler

    scrapy crawl footprints

Or to save it locally.

    scrapy crawl footprints -o footprints.json

## Configuration

The script expects you to create a dotEnv file, named .env, in the project root
directory and with the following entries.

    # Credentials
    USERNAME=YOUR_USERNAME
    PASSWORD=YOUR_PASSWORD

    # URL patterns, used in the footprints.py crawler script to create new URL's
    TICKET_URL_PATTERN=https://YOUR_DOMAIN/MRcgi/MRTicketPage.pl?USER=%s=&CUSTM=%s&MR=%s&...
    START_URL_PATTERN=https://YOUR_DOMAIN/MRcgi/MRhomepage.pl?CUSTM=%s&USER=%s&...

    # Other URLs used by the crawler
    CONFIG_URL=https://YOUR_DOMAIN/MRcgi/MRlogin.pl
    PAGINATION_URL=YOUR_DOMAIN/MRcgi/MRhomepage.pl
