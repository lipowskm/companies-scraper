from docker.errors import APIError
from time import sleep, time
from typing import Callable

from docker.models.containers import Container
from scrapy.crawler import CrawlerProcess, CrawlerRunner
import docker
from twisted.internet import reactor

from spider import Spider2


def crawl_job():
    """
    Job to start spiders.
    Return Deferred, which will execute after crawl has completed.
    """
    settings = {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    }
    runner = CrawlerRunner(settings)
    return runner.crawl(Spider2)


def schedule_next_crawl(null, sleep_time):
    """
    Schedule the next crawl
    """
    reactor.callLater(sleep_time, crawl)


def crawl():
    """
    A "recursive" function that schedules a crawl 30 seconds after
    each successful crawl.
    """
    # crawl_job() returns a Deferred
    d = crawl_job()
    # call schedule_next_crawl(<scrapy response>, n) after crawl job is complete
    d.addCallback(schedule_next_crawl, 5)
    d.addErrback(catch_error)


def catch_error(failure):
    print(failure.value)


def main():
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })
    process.crawl(Spider2)
    process.crawl(Spider2, 5)
    process.crawl(Spider2, 10)
    process.crawl(Spider2, 15)
    now = time()
    process.start()
    finish = time()
    print(f'Exec time {finish - now}')


if __name__ == "__main__":
    main()
