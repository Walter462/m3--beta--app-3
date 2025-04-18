import anvil
import sys
import logging
import traceback
import time
import timeit

def setup_logging(
  logger_name = 'CalcCore',
  enable = True,
  logging_level = logging.DEBUG,
  ):
    '''
    name: 'CalcCore', 
    enable: True, False
    logging_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    '''
    logger = logging.getLogger(logger_name)
    if enable:
      logger.setLevel(logging_level)  # Set the logging_level
      # Check if handlers are already added to avoid duplicate logs
      if not logger.handlers:
          # Create a console handler and set the logging_level to DEBUG or the specified logging_level
          console = logging.StreamHandler(sys.stdout)
          console.setLevel(logging_level)
          # Create a formatter and set it for the console handler
          formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
          console.setFormatter(formatter)
          # Add the handler to the logger
          logger.addHandler(console)
    # If logging is disabled
    else:
        logger.setLevel(logging.NOTSET)  # Disable logging for this logger
        logger.handlers = []  # Remove all handlers
        

def func_calling(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('CalcCore')  # Use the appropriate logger
        logger.info(f"Calling <{func.__name__}>")
        result = func(*args, **kwargs)  # Call the wrapped function
        return result
    return wrapper
    
def print_traceback_stack(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('traceback')
        #logger.debug(f"Calling <{func.__name__}>")
        result = func(*args, **kwargs)
        logger.debug(f"Stack trace for <{func.__name__}>:")
        logger.debug(traceback.print_stack())
        return result
    return wrapper
  
def execution_time_tracking(func):
  def wrapper(*args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    logger = logging.getLogger('CalcCore')
    logger.debug(f"Execution time for <{func.__name__}()> is: {execution_time:.4f} seconds")
    return result
  return wrapper


#@profile # Add this line to enable line_profiler. bash: kernprof -l -v ./server_code/CalcCore.py

def average_function_execution_time(func):
  def wrapper(*args, **kwargs):
    result = func(*args, **kwargs)
    logger = logging.getLogger('CalcCore')
    logger.debug(f"Average execution time for <{func.__name__}()> is: {timeit.timeit(func, number=10):.4f} seconds")
    return result
  return wrapper

# Utils
@anvil.server.callable
def clear_cookies():
  print(f"Cookie {anvil.server.cookies.local} cleared")
  return anvil.server.cookies.local.clear()

@anvil.server.callable
def session_data(key):
  print(f"Got session data {anvil.server.session.get(str(key))}")
