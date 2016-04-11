from scrapy.item import Item, Field

class Issue(Item):

    id = Field()
    description = Field()
    status = Field()
    status2 = Field()
    created = Field()
    last_updated = Field()
    created_updated_diff = Field()
    interactions = Field()
    issuetype = Field()
    first_name = Field()
    last_name = Field()
    parties = Field()
