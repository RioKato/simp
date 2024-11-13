from sys import platform
from .docker import Docker
from .tmux import Tmux

match platform:
    case 'linux':
        from .linux import Standalone, run

    case 'win32':
        from .windows import Standalone, run

__all__ = [
    'Docker',
    'Tmux',
    'Standalone', 'run'
]
