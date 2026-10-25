"""Load KiCad library symbols (resolving 'extends') and report pin geometry."""
import copy, os
from sexp import parse, find, first, Sym

KICAD_SYM = os.environ.get("KICAD_SYM", "/opt/kicad9/usr/share/kicad/symbols")
_cache = {}


def _lib(path):
    if path not in _cache:
        _cache[path] = parse(open(path).read())[0]
    return _cache[path]


def lib_path(lib, extra=None):
    if extra and lib in extra:
        return extra[lib]
    return os.path.join(KICAD_SYM, lib + ".kicad_sym")


def get_symbol(lib_id, extra=None):
    """Return a standalone symbol definition (list) named lib_id, 'extends' flattened."""
    lib, name = lib_id.split(":")
    root = _lib(lib_path(lib, extra))
    syms = {s[1]: s for s in find(root, "symbol")}
    s = copy.deepcopy(syms[name])
    ext = first(s, "extends")
    if ext:
        base = copy.deepcopy(syms[ext[1]])
        # keep derived properties, take graphics/pins from base
        props = {p[1]: p for p in find(s, "property")}
        new = [Sym("symbol"), name]
        for e in base[2:]:
            if isinstance(e, list) and e[0] == "property" and e[1] in props:
                new.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == "symbol":
                sub = copy.deepcopy(e)
                sub[1] = sub[1].replace(ext[1], name, 1)
                new.append(sub)
            else:
                new.append(e)
        for p in props.values():
            new.append(p)
        s = new
    s[1] = lib_id
    for sub in find(s, "symbol"):
        sub[1] = sub[1].split(":")[-1]
    return s


def pins(sym):
    """[(number, name, x, y, angle, length, etype, unit)] in symbol coords (Y up)."""
    out = []
    for sub in find(sym, "symbol"):
        unit = int(sub[1].rsplit("_", 2)[-2])
        for p in find(sub, "pin"):
            at = first(p, "at"); ln = first(p, "length")
            name = first(p, "name")[1]; num = first(p, "number")[1]
            out.append((num, name, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                        float(ln[1]), str(p[1]), unit))
    return out


def prop(sym, key):
    for p in find(sym, "property"):
        if p[1] == key:
            return p[2]
    return None
