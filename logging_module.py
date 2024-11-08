import logging
import os

def setup_logging(verbose=False):
    # disable Matplotlib logging to reduce the output size
    logging.getLogger('matplotlib.font_manager').disabled = True
    log_level = logging.DEBUG if verbose else logging.INFO
    # Set the log file name based on the log level
    logname = 'debug.log' if log_level == logging.DEBUG else 'info.log'

    # Remove the log file if it already exists
    if os.path.exists(logname):
        os.remove(logname)

    # logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    logging.basicConfig(filename=logname,
                        filemode='a',format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', level=log_level)