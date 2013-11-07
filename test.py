import threading
import Queue
import SimpleHTTPServer
import SocketServer
from functools import partial
from pprint import pprint
from requests_debug import debug as requests_debug; requests_debug.install_hook()
import requests
import time
from testfixtures import compare


def make_server():
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    return SocketServer.TCPServer(("", 0), Handler)



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



def test_threading():
    """
    Assert that the thread locals actually work correctly by making requests
    """
    http_server = make_server()
    results_q = Queue.Queue()

    def make_url(path):
        port = http_server.server_address[1]
        return "http://localhost:{0}/".format(port) + path


    client_threads = [
        client_thread(results_q, 0, make_url("test.py")),
        client_thread(results_q, 1, make_url("test.py")),
        client_thread(results_q, 2, make_url("404")),
    ]


    try:
        server_thread = threading.Thread(target=http_server.serve_forever)
        server_thread.start()
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
    finally:
        http_server.shutdown()

    results.sort(key=lambda x: x[0])
    
    # make the results look like the values we care about
    def normalize(results):
        return [
            (thread_id, checkpoint_id,
             [
                    {'method': item['method'],
                     'checkpoint_id': item['checkpoint_id'],
                     'url': item['url']}
                    for item in items
                    ])
            for thread_id, checkpoint_id, items in results
        ]

    compare(normalize(results), [
            (0, results[0][1], [
                    {'method': 'get',
                     'checkpoint_id': results[0][1],
                     'url': make_url("test.py?thread_id=0&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[0][1],
                     'url': make_url("test.py?thread_id=0&n=1")},
                ]),
            (1, results[1][1], [
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'url': make_url("test.py?thread_id=1&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'url': make_url("test.py?thread_id=1&n=1")},
                ]),
            (2, results[2][1], [
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'url': make_url("404?thread_id=2&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'url': make_url("404?thread_id=2&n=1")},
                    ])])



if __name__ == '__main__':
    test_threading()
