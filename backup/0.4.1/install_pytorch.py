"""Automated PyTorch Installer with CUDA auto-detection.
Detects GPU capabilities via nvidia-smi and installs the matching PyTorch build.
"""

import sys
import subprocess
import re

# Supported PyTorch wheel channels
INDEX_URLS = {
    "cu126": "https://download.pytorch.org/whl/cu126",
    "cu124": "https://download.pytorch.org/whl/cu124",
    "cu121": "https://download.pytorch.org/whl/cu121",
    "cu118": "https://download.pytorch.org/whl/cu118",
    "cpu": "https://download.pytorch.org/whl/cpu",
}


def detect_cuda_version() -> str | None:
    """Runs nvidia-smi to find the maximum CUDA version supported by the driver."""
    try:
        output = subprocess.check_output(
            ["nvidia-smi"], stderr=subprocess.STDOUT, text=True
        )
        match = re.search(r"CUDA Version:\s+(\d+\.\d+)", output)
        if match:
            return match.group(1)
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    return None


def select_pytorch_wheel(cuda_ver_str: str | None) -> tuple[str, str]:
    """Selects the best matching PyTorch wheel tag and index URL."""
    if not cuda_ver_str:
        return "cpu", INDEX_URLS["cpu"]

    major, minor = map(int, cuda_ver_str.split("."))

    # Select latest PyTorch build supported by the installed driver
    if (major, minor) >= (12, 6):
        return "cu126", INDEX_URLS["cu126"]
    elif (major, minor) >= (12, 4):
        return "cu124", INDEX_URLS["cu124"]
    elif (major, minor) >= (12, 1):
        return "cu121", INDEX_URLS["cu121"]
    elif (major, minor) >= (11, 8):
        return "cu118", INDEX_URLS["cu118"]
    else:
        print(f"CUDA {cuda_ver_str} is below 11.8. Falling back to CPU build.")
        return "cpu", INDEX_URLS["cpu"]


def main():
    print("Checking system GPU capabilities...")
    cuda_ver = detect_cuda_version()

    if cuda_ver:
        print(f"Detected NVIDIA Driver supporting up to CUDA {cuda_ver}")
    else:
        print("No NVIDIA GPU/Driver detected. Targeting CPU.")

    wheel_tag, index_url = select_pytorch_wheel(cuda_ver)
    print(f"Selected PyTorch target: [{wheel_tag}] ({index_url})")

    # Command: python -m pip install torch torchvision torchaudio --index-url <url>
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        index_url,
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")
    try:
        subprocess.check_call(cmd)
        print("\nPyTorch installation complete!")
    except subprocess.CalledProcessError as err:
        print(f"\nInstallation failed with error code: {err.returncode}", file=sys.stderr)
        sys.exit(err.returncode)


if __name__ == "__main__":
    main()