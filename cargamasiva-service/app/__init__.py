# app/__init__.py
# Mantiene compatibilidad con:
#   - import app.utils                  (tu módulo app/utils.py)
#   - from app.utils.csv_utils import X (tests que esperan submódulo)

import sys
import types

try:
    from . import utils as _utils  # este es tu archivo app/utils.py
except Exception:  # pragma: no cover
    _utils = None

if _utils is not None:
    # 1) Exponer 'app.utils' como "paquete" pero con el contenido de tu módulo utils.py
    utils_pkg = types.ModuleType("app.utils")
    utils_pkg.__path__ = []  # lo marca como paquete para el import system

    # Copiamos todos los atributos del módulo original (app/utils.py)
    for name in dir(_utils):
        if not name.startswith("__") or name in {"__doc__", "__all__"}:
            setattr(utils_pkg, name, getattr(_utils, name))

    # Registramos 'app.utils' apuntando al "paquete" con el contenido del módulo
    sys.modules["app.utils"] = utils_pkg

    # 2) Crear alias 'app.utils.csv_utils' que exporta lo mismo que app/utils.py
    csv_mod = types.ModuleType("app.utils.csv_utils")
    for name in dir(_utils):
        if not name.startswith("__") or name in {"__doc__", "__all__"}:
            setattr(csv_mod, name, getattr(_utils, name))

    sys.modules["app.utils.csv_utils"] = csv_mod
