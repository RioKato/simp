from argparse import ArgumentParser
from contextlib import suppress
from pathlib import Path
from subprocess import run
from sys import stderr


def pprint(item: Path):
    RED = '\033[31m'
    END = '\033[0m'
    symlink = item.readlink()

    if item.exists():
        message = f'{RED}[Replaced SymLink]{END} {item}: {symlink}'
    else:
        message = f'{RED}[Replaced SymLink]{END} {item}: Not Found({symlink})'

    print(message, file=stderr)


def relink(sysroot: Path):
    if not sysroot.exists():
        raise FileNotFoundError

    for path, dirs, files in sysroot.walk():
        for item in dirs + files:
            item = path.joinpath(item)

            if not item.is_symlink():
                continue

            symlink = item.readlink()

            if not symlink.is_absolute():
                continue

            symlink = symlink.relative_to(symlink.root)
            symlink = sysroot.joinpath(symlink)
            symlink = symlink.relative_to(item.parent, walk_up=True)

            with suppress(FileNotFoundError):
                item.unlink()

            item.symlink_to(symlink)
            pprint(item)


def docker_cpall(image: str) -> str:
    command = ['docker', 'create', image]
    cid = run(command, check=True, capture_output=True, text=True).stdout.strip()

    try:
        out = image.replace(':', '_')
        command = ['docker', 'cp', f'{cid}:/', out]
        run(command, check=True)

    finally:
        command = ['docker', 'rm', '-v', cid]
        run(command, check=True)

    return out


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--docker', action='store_true')
    parser.add_argument('image')
    args = parser.parse_args()
    out = args.image

    if args.docker:
        out = docker_cpall(out)

    relink(Path(out))
