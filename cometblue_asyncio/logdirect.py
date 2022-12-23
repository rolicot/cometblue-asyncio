#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A highly efficient logging module which performs logging with direct calls to
writer functions or no-op functions.

Import this module as:
    import logdirect
    log = logdirect.Logger(__name__)

Then perform logging by calling methods of log:
    log.error(s, *args, **kwargs):
    log.warning(s, *args, **kwargs):
    log.info(s, *args, **kwargs):
    log.debug(s, *args, **kwargs):
    log.tracing(s, *args, **kwargs):
        Performs formatted logging by s.format(*args, **kwargs), e.g.:

        log.warning('Hey, the thing {thing} has problems with {} and {}.',
                        problem1, problem2, thing=something)

        This has the advantage that string formatting is not performed if the
        logging does not apply (i.e. if the specified logging level is above
        configured logging level).

    log.error_(*args):
    log.warning_(*args):
    log.info_(*args):
    log.debug_(*args):
    log.tracing_(*args):
        Performs print-like logging (list of args), e.g.:

        log.info_('Starting conversion...')
        log.error_('Problem number ', number, ' occurred.')

The special functions log.die(s, *args, **kwargs) and log.die_(*args) call
the respective error() or error_() and then kill the program using sys.exit(1).

If you want to avoid calling expensive functions to get the data for logging,
use e.g.:
    if log.info_on:
        log.info('This {} was expensive to calculate.', expensive_func())
    dtto with error_on, warning_on, debug_on, tracing_on
'''
__author__ = 'Pavel Krc'
__email__ = 'src@pkrc.net'
__version__ = '1.1'
__date__ = '2022-11'

import sys
from datetime import datetime


levels = {
    'ERROR'  : 10,
    'WARNING': 20,
    'INFO'   : 30,
    'DEBUG'  : 40,
    'TRACING': 50,
    }

datefmt = '%Y-%m-%d %H:%M:%S'
default_level = levels['INFO']
stderr_from = levels['WARNING']

levels_r = {v: n for n, v in levels.items()}
module_levels = {}
registered_loggers = []
now = datetime.now

def noop(*args, **kwargs):
    """Logging method that does nothing (the specified logging level is disabled)."""
    pass

def mklogger(log_type, level, module, fout):
    """Prepares a logger method with the given parameters.

    The prepared method works directly without any "if"s, mostly with one print
    command.
    """
    fmt = [datefmt]
    if module:
        fmt.extend([' ', module])
    fmt.extend([' ', level, ':'])
    fmt = ''.join(fmt)

    if log_type == 'f':
        # formatted logging (see module doc)
        return lambda s, *args, **kwargs: print(
                now().strftime(fmt), s.format(*args, **kwargs), file=fout)
    elif log_type == 'p':
        # print-like logging (list of args; see module doc)
        return lambda *args: print(now().strftime(fmt), *args, file=fout)

class Logger:
    """Main logger class.

    Provides logging methods for the specified levels according to
    configuration. Upon configuration, the methods are directly assigned as
    loggers or dummy no-op methods, so there is no checking done at logging
    time.
    """
    def __init__(self, modulename=None, custom_level=None):
        self.module = modulename
        self.reinit(custom_level)
        registered_loggers.append(self)

    def reinit(self, new_level=None):
        """(Re)initialize logger with specified level or (module) default level"""

        if new_level is None:
            level = module_levels.get(self.module, default_level)
        else:
            level = new_level

        for lname, lnum in levels.items():
            lnamel = lname.lower()
            if lnum > level:
                setattr(self, lnamel, noop)
                setattr(self, lnamel+'_', noop)
                setattr(self, lnamel+'_on', False)

            else:
                fout = sys.stderr if lnum <= stderr_from else sys.stdout

                setattr(self, lnamel, mklogger('f', lname, self.module, fout))
                setattr(self, lnamel+'_', mklogger('p', lname, self.module, fout))
                setattr(self, lnamel+'_on', True)

    def die(self, s, *args, **kwargs):
        """Call error(s, *args, **kwargs) and sys.exit(1)"""
        self.error(s, *args, **kwargs)
        sys.exit(1)

    def die_(self, *args):
        """Call error_(*args) and sys.exit(1)"""
        self.error_(*args)
        sys.exit(1)

def reinit_all_loggers(custom_level=None):
    for logger in registered_loggers:
        logger.reinit(custom_level)

def configure(level_default, level_per_module={}):
    global default_level, module_levels

    default_level = levels[level_default]
    module_levels = {k: levels[v] for k, v in level_per_module.items()}
    reinit_all_loggers()
