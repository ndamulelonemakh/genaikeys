# Logging

The package logger is silent by default and installs a `NullHandler`, so
GenAIKeys never spams your application logs unless you ask it to.

## Enable / disable

```python
from genaikeys import enable_logging, disable_logging

enable_logging()                       # INFO to stderr
enable_logging(level="DEBUG")          # full trace
enable_logging(handler=my_handler)     # custom sink
disable_logging()                      # back to silent
```

## Production usage

Configure the `genaikeys` logger through the standard `logging` module:

```python
import logging

logging.getLogger("genaikeys").setLevel(logging.INFO)
```
