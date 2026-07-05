"""Tiny structured logger used across refundpilot."""

import logging

_base = logging.getLogger("refundpilot")


class _Log:
    def _emit(self, level, msg, **fields):
        kv = " ".join(f"{k}={v}" for k, v in fields.items())
        _base.log(level, "%s %s", msg, kv)

    def info(self, msg, **fields):
        self._emit(logging.INFO, msg, **fields)

    def warning(self, msg, **fields):
        self._emit(logging.WARNING, msg, **fields)


log = _Log()
