from sys import platform
from .cmd import Cmd
from .docker import Docker
from .tmux import Tmux

match platform:
    case 'linux':
        from .linux import Standalone, execcmd

    case 'win32':
        from .windows import Standalone, execcmd

__all__ = [
    'Cmd',
    'Docker',
    'Tmux',
    'Standalone', 'execcmd'
]
