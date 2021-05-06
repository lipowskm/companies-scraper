from html import unescape

from scrapy.item import Item, Field


def serialize_reviews(value):
    return unescape(value)


class Place(Item):
    title = Field()
    address = Field()
    phone = Field()
    page = Field()
    rating = Field()
    reviews = Field(serializer=int)
