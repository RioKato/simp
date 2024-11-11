from sys import platform
from .cmd import Cmd
from .docker import Docker
from .tmux import Tmux

match platform:
    case 'linux':
        from .linux import Standalone, run

    case 'win32':
        from .windows import Standalone, run

__all__ = [
    'Cmd',
    'Docker',
    'Tmux',
    'Standalone', 'run'
]
