import threading
import Queue
import SimpleHTTPServer
import SocketServer
from functools import partial
from pprint import pprint
from requests_debug import debug as requests_debug
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


def start_server():
    http_server = make_server()
    server_thread = threading.Thread(target=http_server.serve_forever)
    server_thread.start()
    return http_server, server_thread


def stop_server(http_server):
    http_server.shutdown()    


def server_port(http_server):
    return http_server.server_address[1]


def test_uninstall_hook():
    def assert_items(items_cb):
        http_server, _ = start_server()
        url = make_url(server_port(http_server),
                       "test.py")
        requests.get(url)
        stop_server(http_server)
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
             'url': item['url']}
            for item in items
            ]    


def test_threading():
    """
    Assert that the thread locals actually work correctly by making requests
    """
    requests_debug.install_hook()
    http_server, _ = start_server()
    make_url_ = partial(make_url, server_port(http_server))
    results_q = Queue.Queue()


    client_threads = [
        client_thread(results_q, 0, make_url_("test.py")),
        client_thread(results_q, 1, make_url_("test.py")),
        client_thread(results_q, 2, make_url_("404")),
    ]


    try:
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
        stop_server(http_server)

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
                     'url': make_url_("test.py?thread_id=0&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[0][1],
                     'url': make_url_("test.py?thread_id=0&n=1")},
                ]),
            (1, results[1][1], [
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'url': make_url_("test.py?thread_id=1&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[1][1],
                     'url': make_url_("test.py?thread_id=1&n=1")},
                ]),
            (2, results[2][1], [
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'url': make_url_("404?thread_id=2&n=0")},
                    {'method': 'get',
                     'checkpoint_id': results[2][1],
                     'url': make_url_("404?thread_id=2&n=1")},
                    ])])



if __name__ == '__main__':
    test_threading()
