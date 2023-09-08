## Module not found error when importing from benlp

### Fix 1 (Not recommended)

Import the absolute path to the project and append it to the `sys.path` variable in every file.

```python
from dotenv import load_dotenv
import os
import sys
load_dotenv(".env")
package_path = os.environ.get("PACKAGE_PATH")
sys.path.append(package_path)
```

### Fix 2 (Recommended)

1. Run `python -c "import site; print(site.getsitepackages())` to get the path to the site-packages directory. This should be in your venv.

2. Create a `.pth` file in the site-packages directory called `benlp.pth`. This file should contain the absolute path to the project.

benlp.pth
```
/absolute/path/to/root/project/folder
```

3. Fixed! You can now import from benlp.