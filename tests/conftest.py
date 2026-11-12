"""pytest 的全局夹具与路径配置。

conftest.py 会先于测试模块被导入，因此可以在这里
把项目根目录加入 sys.path，保证 `from poker.xxx import ...` 可用。
"""

import sys
from pathlib import Path

# 当前文件是 tests/conftest.py，parents[1] 即项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
