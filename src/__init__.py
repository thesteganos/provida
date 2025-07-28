
"""Inicialização do pacote principal."""

import importlib
import sys

if 'app' not in sys.modules:
    sys.modules['app'] = importlib.import_module('src.app')
