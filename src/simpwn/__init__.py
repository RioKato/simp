from sys import platform
from .glibc import demangle, mangle, protect, reveal
from .r2dr import r2dr64le
from .utility import block, iota, p16, p32, p64, p8, pd, pf, rol64, ror64, u16, u32, u64, u8, ud, uf


match platform:
    case 'linux':
        from .linux import EasyDevelopment
    case 'windows':
        from .windows import EasyDevelopment

__all__ = [
    'demangle', 'mangle', 'protect', 'reveal',
    'r2dr64le',
    'block', 'iota', 'p16', 'p32', 'p64', 'p8', 'pd', 'pf', 'rol64', 'ror64', 'u16', 'u32', 'u64', 'u8', 'ud', 'uf',
    'EasyDevelopment'
]
