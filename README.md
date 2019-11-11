> pip install python-gcp-injections

If you want single line logging you can use standard logging with `logging.info("This is my log text")`. But if you 
would like to have som more context you use.

```python
from gcpi.stackdriverlog import get_logger
LOG = get_logger()

my_dict_data = {'test':1, 'debug':2}

LOG.info("This is my log")
LOG.info(my_dict_data, param1='true', message="Invoice render timing")
``` 
message is the text that will show up as summary in the log. My dict_data in this case 
will show up under jsonPayload event, while the param1 will show up on the same level
as event. 

### Django
in settings.py add
```python
from gcpi.stackdriverlog import stackdriver_init_logging
stackdriver_init_logging()
```

