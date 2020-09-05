import fnmatch
import re
from pathlib import Path


def find_includes(lines):
    files = [[l.strip()[len("IncludeFile"):].strip()[len("="):].strip(),a+1] for a,l in enumerate(lines) if l.strip().startswith("IncludeFile")]
    return files


def find_scripts(lines):
    files = [[l.strip()[len("ScriptPath"):].strip()[len("="):],a+1] for a,l in enumerate(lines) if l.strip().startswith("ScriptPath")]
    return files


def find_files(lines):
    files = [[l.strip()[len("FilePath"):].strip()[len("="):].strip(),a+1] for a,l in enumerate(lines) if l.strip().startswith("FilePath")]
    return files


def find_lua_includes(lines):
    files = [[l.split('"')[1], a+1] for a,l in enumerate(lines) if ("dofile(" in l) and not ("require" in l or "--dofile" in l)]
    return files


def find_lua_require(lines):
    files = []
    for a,l in enumerate(lines):
        if "require(" in l:
            s = l.split('"')
            if len(s) == 1:
                s = l.split("'")
            if len(s) == 1:
                files.append(["?", a])
                continue
            files.append([s[1], a])

    return files


def check_path(path):
    if "FilePath" in path:
        print("extra FilePath")
        path = path.split("=")[-1].strip()
    if '\\' in path:
        print("WinPath")
        path = path.replace("\\", "/")
    if Path(path).exists():
        return 0
    else:
        g = [f"{f}" for f in Path('.').glob(f"**/*{Path(path).suffix}")]

        low = [l.lower() for l in g]

        if path.lower() in low:
            return g[low.index(path.lower())]
        else:
            return 2


def check_file_path(path):
    if "FilePath" in path:
        print("extra FilePath")
        path = path.split("=")[-1].strip()
    if '\\' in path:
        print("WinPath")
        path = path.replace("\\", "/")
    p = Path(path)
    temp = path[:-len(p.suffix)] + '*' + p.suffix
    t_glob = [f for f in Path('.').glob(temp)]
    if t_glob != []:
        return 0
    else:
        low = [f"{l}".lower() for l in t_glob]
        i = 0
        g  = [f"{f}" for f in Path('.').glob(f"**/*{p.suffix}")]
        g_low = [f.lower() for f in g]
        for l in low:
            if l in g_low:
                return g[g_low.index(l)]

        return 2


def check_require_path(path):
    temp = '**/'+path+'.lua'
    t_glob = [f for f in Path('.').glob(temp)]
    return t_glob != []


all_inis = Path('.').glob('**/*.ini')
all_luas = Path('.').glob('**/*.lua')
all_includes = []

for p in all_inis:
    with p.open() as f:
        lines = [l for l in f.readlines()]
        all_includes = find_includes(lines)
        all_scripts = find_scripts(lines)
        all_files = find_files(lines)
        for l in all_includes:
            c = check_path(l[0].strip())
            if c != 0:
                print("INCLUDE check {p}:[l[1]]")
                if c == 2:
                    print(f"missing {l[0]}")
                else:
                    print(f"found here {c}, missing {l[0]}")
        for l in all_scripts:
            c = check_path(l[0].strip())
            if c!=0:
                print(f"LUA check {p}:{l[1]}")
                if c==2:
                    print(f"missing {l[0]}")
                else:
                    print(f"found here {c}, missing {l[0]}")
        for l in all_files:
            c = check_file_path(l[0].strip())
            if c!=0:
                print(f"FILES check {p} line {l[1]}")
                if c==2:
                    print(f"missing {l[0]}")
                else:
                    print(f"found at {c} missing {l[1]}")

for p in all_luas:
    with p.open() as f:
        lines = [l for l in f.readlines()]
        all_lua_includes = find_lua_includes(lines)
        all_lua_require = find_lua_require(lines)
        for l in all_lua_includes:
            if not check_path(l[0]):
                print(f"LUA_INCLUDE check {p}:{l[1]}")
                print(l[0])

        for l in all_lua_require:
            if l[0] == "?":
                print(f"??? check {p} at line {l[1]}")
                continue
            if not check_require_path(l[0]):
                print(f"LUA_REQUIRE check {p} line {l[1]}")
                print(l[0])