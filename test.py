import threading
import Queue
from wsgiref.simple_server import make_server
from functools import partial
from pprint import pprint
from requests_debug import debug as requests_debug
import requests
import time
from testfixtures import compare
from contextlib import contextmanager
import logging
logging.basicConfig(level=logging.DEBUG)



def client_thread_target(results_q, thread_id, url):
    for n in xrange(2):
        requests.get(
            url, 
            params=[("thread_id", thread_id), ("n",n)]
        )
        
    results_q.put(
            (thread_id, requests_debug.checkpoint_id(), requests_debug.items())
    )


def client_thread(results_q, thread_id, url):
    return threading.Thread(
        target=partial(
            client_thread_target,
            results_q, 
            thread_id,
            url,
            )
        )


@contextmanager
def start_server():
    def app(environ, start_response):
        if "error" in environ.get('PATH_INFO', ''):
            start_response("302 Moved Temporarily", [
                    ("Location", environ['PATH_INFO'])])
            return []
        elif "404" in environ.get('PATH_INFO', ''):
            start_response("404 Not Found", [])
            return []
        else:
            start_response("200 OK", [])
            return ["ok."]

    http_server = make_server('', 0, app)
    server_thread = threading.Thread(target=http_server.serve_forever)
    server_thread.start()
    yield http_server
    stop_server(http_server)


def stop_server(http_server):
    http_server.shutdown()


def server_port(http_server):
    return http_server.server_address[1]


def test_exception():
    requests_debug.install_hook()
    with start_server() as http_server:
        url = make_url(
            server_port(http_server),
            "error/")

        try:
            requests.get(url)
        except requests.TooManyRedirects, e:
            stop_server(http_server)
            compare(
                normalize_items(requests_debug.items()),
                [{'checkpoint_id': requests_debug.checkpoint_id(),
                  'method': 'get',
                  'status': None,
                  'url': url}])



def test_uninstall_hook():
    def assert_items(items_cb):
        with start_server() as http_server:
            url = make_url(server_port(http_server),
                           "test.py")
            requests.get(url)

        compare(
            normalize_items(requests_debug.items()),
            items_cb(url)
        )

    # install the hook
    requests_debug.install_hook()
    # assert that the hook is working
    assert_items(lambda url: [
            {'method': 'get',
             'checkpoint_id': requests_debug.checkpoint_id(),
             'status': 200,
             'url': url}
            ])

    # uninstall the hook
    requests_debug.uninstall_hook()
    # assert that nothing is recorded when we uninstall the hook
    assert_items(lambda url: [])
    

def make_url(port, path):
    return "http://localhost:{0}/".format(port) + path


# make the results look like the values we care about
def normalize_items(items):
    return [
            {'method': item['method'],
             'checkpoint_id': item['checkpoint_id'],
             'status': item['status'],
             'url': item['url']}
            for item in items
            ]    


def test_threading():
    """
    Assert that the thread locals actually work correctly by making requests
    """
    with start_server() as http_server:
        requests_debug.install_hook()
        make_url_ = partial(make_url, server_port(http_server))
        results_q = Queue.Queue()


        client_threads = [
            client_thread(results_q, 0, make_url_("test.py")),
            client_thread(results_q, 1, make_url_("test.py")),
            client_thread(results_q, 2, make_url_("404")),
        ]


        # use an ordered dict to keep things sorted
        # as we collect the results
        results = []

        for client in client_threads:
            client.start()

        for client in client_threads:
            # we may not get the result for the client
            # we're on but we need to collect that many
            # values, so this is a quick way to do that.

            # this may timeout and return None if a request
            # takes longer than 2 seconds (it shouldn't)
            results.append(results_q.get(True, 2))


    results.sort(key=lambda x: x[0])

    def normalize(results):
        return [
            (thread_id, checkpoint_id, normalize_items(items))
            for thread_id, checkpoint_id, items in results
        ]
    
    compare(normalize(results), [
            (0, results[0][1], [
                    {'method': 'get',
                     'checkpoint_id': results[0][1],
                     'status': 200,
                     'url': make_url_("test.py?thread_id=0&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[0][1],
                     'status': 200,
                     'url': make_url_("test.py?thread_id=0&n=1")},
                ]),
            (1, results[1][1], [
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'status': 200,
                     'url': make_url_("test.py?thread_id=1&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'status': 200,
                     'url': make_url_("test.py?thread_id=1&n=1")},
                ]),
            (2, results[2][1], [
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'status': 404,
                     'url': make_url_("404?thread_id=2&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'status': 404,
                     'url': make_url_("404?thread_id=2&n=1")},
                    ])])



if __name__ == '__main__':
    test_threading()
