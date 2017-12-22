requests_debug
==============

Debugging for the requests library


Usage
-------

Once you install the hook, `requests_debug` will track all the requests made with
requests:

```python
>>> import requests
>>> from requests_debug import debug
>>> from pprint import pprint
>>>
>>> debug.install_hook()
>>> requests.get("http://httpbin.org/get")
<Response [200]>
>>> requests.get("http://httpbin.org/status/418")
<Response [418]>
>>>
>>> pprint(debug.items())
[{'method': 'get',
  'status': 200,
  'time': '0.869',
  'time_float': 0.8693149089813232,
  'url': 'http://httpbin.org/get'},
 {'method': 'get',
  'status': 418,
  'time': '0.250',
  'time_float': 0.25032901763916016,
  'url': 'http://httpbin.org/status/418'}]
>>> debug.clear_items()
>>> debug.items()
[]
>>> debug.uninstall_hook()
>>>
```

Requests are also logged using the "request_debug" logger at level "DEBUG". Exceptions
That occur when making the request are logged at level "ERROR".
