import logging

def setup_logging(verbose=False):
    # disable Matplotlib logging to reduce the output size
    logging.getLogger('matplotlib.font_manager').disabled = True
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')