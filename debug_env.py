import sys
import os
import site

print("Python Version:", sys.version)
print("\nPython Executable:", sys.executable)
print("\nPython Path:")
for path in sys.path:
    print(f"  - {path}")

print("\nCurrent Working Directory:", os.getcwd())
print("\nAbsolute Path to tools directory:", os.path.abspath("tools"))
print("\nContents of tools directory:", os.listdir("tools") if os.path.exists("tools") else "Directory not found")

try:
    import tools
    print("\ntools module found at:", tools.__file__)
except ImportError as e:
    print("\nFailed to import tools:", str(e))

print("\nEnvironment Variables:")
for key, value in os.environ.items():
    if "PYTHON" in key or "PATH" in key:
        print(f"  {key}: {value}") 