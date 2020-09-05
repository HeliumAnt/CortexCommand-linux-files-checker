from tempfile import mkstemp
from shutil import move, copymode
from pathlib import Path
from os import fdopen
import sys, getopt


verbose = False
fix = True
ask = True


def find_includes(lines):
    """Find all include paths in lines"""
    files = [[l.strip()[len("IncludeFile"):].strip()[len("="):].strip(),a+1] for a,l in enumerate(lines) if l.strip().startswith("IncludeFile")]
    return files


def find_scripts(lines):
    """Find all script paths in lines"""
    files = [[l.strip()[len("ScriptPath"):].strip()[len("="):],a+1] for a,l in enumerate(lines) if l.strip().startswith("ScriptPath")]
    return files


def find_files(lines):
    """Find all file paths in lines"""
    files = [[l.strip()[len("FilePath"):].strip()[len("="):].strip(),a+1] for a,l in enumerate(lines) if l.strip().startswith("FilePath")]
    return files


def find_lua_includes(lines):
    """Find all lua dofile includes from lines"""
    files = [[l.split('"')[1], a+1] for a,l in enumerate(lines) if ("dofile(" in l) and not ("require" in l or "--dofile" in l)]
    return files


def find_lua_require(lines):
    """find all lua require includes from lines
    """
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
    """Check if path exists in file system
    returns
    0 if path found
    found_path(string) if found path with different casing
    """
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
    """
    Check if FilePath exists in filesystem, checks for all path*.pathsuffix
    returns:
    0 if path found
    found_path(string) if found path with different casing
    2 if path is missing
    """
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
    """
    Check if lua require Path exists in filesystem
    returns:
    0 if path found
    found_path(string) if found path with different casing
    2 if path is missing
    """
    if '\\' in path:
        print("WinPath")
        path = path.replace("\\", "/")
    temp = '**/'+path+'.lua'
    t_glob = [f for f in Path('.').glob(temp)]
    if t_glob != []:
        return 0
    else:
        low = [f"{l}".lower() for l in t_glob]
        i = 0


def fix_path(in_file, old_path, rep_path):
    """
    """
    fh, abs_path = mkstemp()

    temp = Path(fh)

    with fdopen('w') as new_file:
        with in_file.open() as old_file:
            for line in old_file:
                new_file.write(line.replace(old_path, rep_path))
    copymode(in_file, abs_path)
    in_file.unlink()
    move(abs_path, in_file)


def ask_user(in_file, old_path, rep_path):
    """
    """
    boo = input('[i]gnore, [r]eplace in file')

    if boo.startswith('i'):
        return
    elif boo.startswith('r'):
        fix_path(in_file, old_path, rep_path)


def inis():
    all_inis = Path('.').glob('**/*.ini')
    for p in all_inis:
        with p.open() as f:
            lines = [l for l in f.readlines()]
            all_includes = find_includes(lines)
            all_scripts = find_scripts(lines)
            all_files = find_files(lines)
            for l in all_includes:
                c = check_path(l[0].strip())
                if c != 0:
                    if c == 2:
                        if verbose:
                            print("INCLUDE check {p}:[l[1]]")
                            print(f"missing {l[0]}")
                    else:
                        if ask or verbose:
                            print("INCLUDE check {p}:[l[1]]")
                            print(f"found here {c}, missing {l[0]}")
                        if ask:
                            ask_user(p, l[0], c)
                        else:
                            fix_path(p, l[0], c)

            for l in all_scripts:
                c = check_path(l[0].strip())
                if c!=0:
                    if c == 2:
                        if verbose:
                            print("LUA check {p}:[l[1]]")
                            print(f"missing {l[0]}")
                    else:
                        if ask or verbose:
                            print("LUA check {p}:[l[1]]")
                            print(f"found here {c}, missing {l[0]}")
                        if ask:
                            ask_user(p, l[0], c)
                        else:
                            fix_path(p, l[0], c)
            for l in all_files:
                c = check_file_path(l[0].strip())
                if c!=0:
                    if c == 2:
                        if verbose:
                            print("FILES check {p}:[l[1]]")
                            print(f"missing {l[0]}")
                    else:
                        if ask or verbose:
                            print("FILES check {p}:[l[1]]")
                            print(f"found here {c}, missing {l[0]}")
                        if ask:
                            ask_user(p, l[0], c)
                        else:
                            fix_path(p, l[0], c)


def lua():
    all_luas = Path('.').glob('**/*.lua')
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



if __name__ == "__main__":
    inis = True
    lua = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvyiln")
    except getopt.GetoptError:
        print('file_check.py [-hvyiln]')
        sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print('file_check.py [-hvyiln]')
                sys.exit()
            elif opt == '-v':
                verbose = True
            elif opt == '-y':
                ask = False
            elif opt == '-i':
                inis = False
            elif opt == '-l':
                lua = False
        if inis:
            inis()
        if lua:
            lua()
