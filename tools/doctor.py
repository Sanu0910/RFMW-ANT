#!/usr/bin/env python3
"""Check that every tool and MCP server this repository uses is installed and answers.

    python3 tools/doctor.py            # tools + MCP servers from .mcp.json
    python3 tools/doctor.py --no-mcp   # tools only

Each MCP server is started exactly as Claude Code starts it (command/args from .mcp.json, run from the
repository root) and must answer the JSON-RPC `initialize` and `tools/list` requests.
Exit code 0 when everything required passes; optional tools only warn.
"""
import json, os, shutil, subprocess, sys, threading, queue, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G, Y, R, N = '\033[32m', '\033[33m', '\033[31m', '\033[0m'
fails = 0


def show(ok, name, info, required=True):
    global fails
    tag = f'{G}OK  {N}' if ok else (f'{R}FAIL{N}' if required else f'{Y}WARN{N}')
    if not ok and required:
        fails += 1
    print(f'  {tag} {name:28s} {info}')


def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return p.returncode == 0, (p.stdout + p.stderr).strip().splitlines()[-1:] or ['']
    except Exception as e:  # noqa: BLE001
        return False, [str(e)]


def check_tools():
    print('Tools')
    py = os.path.join(ROOT, '.venv', 'bin', 'python')
    py = py if os.path.exists(py) else sys.executable
    for name, cmd, req in [
        ('git', 'git --version', True),
        ('git remote push access', 'git ls-remote --heads origin >/dev/null && echo reachable', True),
        ('node (>=18)', 'node --version', True),
        ('claude (Claude Code CLI)', 'claude --version', True),
        ('python deps (.venv)', f'"{py}" -c "import numpy,scipy,matplotlib,shapely,ezdxf,PIL,skrf; print(\'ok\')"', True),
        ('openEMS + CSXCAD', '/opt/openEMS/venv/bin/python -c "import openEMS,CSXCAD; print(\'ok\')"', True),
        ('solidcraft-cli', 'solidcraft-cli --version', True),
        ('KiCad 9 (kicad-cli)', '(command -v kicad-cli >/dev/null && kicad-cli version) || chroot /opt/kicad9 kicad-cli version', True),
        ('Hertzon', '/opt/hertzon-venv/bin/python -c "import hertzon; print(hertzon.__version__ if hasattr(hertzon, \'__version__\') else \'ok\')"', False),
        ('gds2openEMS', '/opt/openEMS/venv/bin/python -c "import gds2openEMS" 2>/dev/null || ls ~/gds2openEMS >/dev/null && echo ok', False),
        ('KiCadRoutingTools', 'test -d /opt/KiCadRoutingTools && echo ok', False),
        ('Playwright Chromium (PDF reports)', 'NODE_PATH=$(npm root -g) node -e "require(\'playwright\')" && echo ok', False),
        ('GNU Octave (MATLAB scripts)', 'octave --version 2>/dev/null | head -1', False),
    ]:
        ok, out = run(cmd)
        show(ok, name, out[0][:70], req)


def mcp_check(name, spec, timeout=90):
    cmd = [spec['command']] + spec.get('args', [])
    env = dict(os.environ, **spec.get('env', {}))
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, bufsize=1)
    except FileNotFoundError as e:
        return False, f'cannot start: {e}'
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l) for l in p.stderr], daemon=True).start()

    def send(obj):
        p.stdin.write(json.dumps(obj) + '\n'); p.stdin.flush()

    def wait(id_, t_end):
        while time.time() < t_end:
            try:
                line = q.get(timeout=0.5)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get('id') == id_:
                return msg
        return None
    t_end = time.time() + timeout
    try:
        send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'doctor', 'version': '1'}}})
        r = wait(1, t_end)
        if not r or 'result' not in r:
            tail = (err[-1].strip() if err else 'no answer')[:90]
            return False, f'no initialize reply ({tail})'
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        r = wait(2, t_end)
        n = len(r['result'].get('tools', [])) if r and 'result' in r else 0
        srv = r and 'result' in r
        return bool(srv), f'{n} tools'
    finally:
        p.kill()


def check_mcp():
    print('MCP servers (.mcp.json)')
    cfg = json.load(open(os.path.join(ROOT, '.mcp.json')))['mcpServers']
    enabled = set(json.load(open(os.path.join(ROOT, '.claude', 'settings.json'))).get('enabledMcpjsonServers', []))
    for name, spec in cfg.items():
        ok, info = mcp_check(name, spec)
        if name not in enabled:
            info += '  (not in enabledMcpjsonServers)'
        show(ok, name, info, required=name != 'hertzon')


if __name__ == '__main__':
    check_tools()
    if '--no-mcp' not in sys.argv:
        check_mcp()
    print(f'\n{G}All required checks passed.{N}' if not fails else f'\n{R}{fails} required check(s) failed.{N} See LOCAL_SETUP.md.')
    sys.exit(1 if fails else 0)
