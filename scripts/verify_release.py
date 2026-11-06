"""Test the actual archive after extraction to a path containing spaces."""

from pathlib import Path
import os
import platform
import subprocess
import tempfile
import zipfile


def main() -> None:
    archives = list(Path("dist").glob("GreenOly-*.zip"))
    if len(archives) != 1:
        raise RuntimeError(f"Expected one archive, found {archives}")
    with tempfile.TemporaryDirectory(prefix="GreenOly portable test ") as tmp:
        if platform.system() == "Darwin":
            subprocess.run(["ditto", "-x", "-k", str(archives[0]), tmp], check=True)
        else:
            with zipfile.ZipFile(archives[0]) as z:
                z.extractall(tmp)
                for entry in z.infolist():
                    mode = entry.external_attr >> 16
                    if mode:
                        (Path(tmp) / entry.filename).chmod(mode & 0o777)
        name = "GreenOly.exe" if os.name == "nt" else "GreenOly"
        executable = Path(tmp) / "GreenOly" / name
        # No user browser cache may be used to pass this test.
        env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(Path(tmp) / "empty cache"))
        subprocess.run([str(executable), "--self-test"], cwd=tmp, env=env, check=True)


if __name__ == "__main__":
    main()
