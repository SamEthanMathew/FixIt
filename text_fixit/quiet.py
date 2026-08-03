#!/usr/bin/env python
"""
Silence PyBullet's C-level chatter (the "No inertial data for link" b3Warnings it prints straight
to the process stdout/stderr file descriptors, which Python-level redirection can't catch).

Usage:
    with quiet():
        p.loadURDF(...)
"""
import contextlib
import os
import sys


@contextlib.contextmanager
def quiet():
    sys.stdout.flush()
    sys.stderr.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = (os.dup(1), os.dup(2))
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        os.close(saved[0])
        os.close(saved[1])
        os.close(devnull)
