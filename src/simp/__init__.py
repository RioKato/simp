from sys import platform
from .docker import Docker
from .simp import Bridge, Executor, Launcher, config
from .tmux import Tmux

__all__ = [
    'Docker',
    'Bridge', 'Executor', 'Launcher', 'config',
    'Tmux',
]

match platform:
    case 'linux':
        from .linux import SocketBridge, Standalone
        __all__.extend(['SocketBridge', 'Standalone'])

    case 'windows':
        from .windows import SocketBridge, Standalone, WSAStartup, WinSocket
        __all__.extend(['SocketBridge', 'Standalone', 'WSAStartup', 'WinSocket'])
