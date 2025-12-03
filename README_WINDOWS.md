# Windows Installation Guide

This guide explains how to run the Parallel Inference Stack on Windows using WSL 2 (Windows Subsystem for Linux).

## Prerequisites

1.  **WSL 2**: Ensure you have WSL 2 installed with a Linux distribution (e.g., Ubuntu).
    *   [Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
2.  **Docker Desktop**: Install Docker Desktop for Windows and enable the WSL 2 backend.
    *   [Install Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)
    *   Ensure "Use the WSL 2 based engine" is checked in Docker Desktop settings > General.
3.  **NVIDIA Drivers (Optional)**: If you have an NVIDIA GPU and want to use it for inference, install the latest Game Ready or Studio drivers.
    *   [Download NVIDIA Drivers](https://www.nvidia.com/Download/index.aspx)
    *   WSL 2 supports GPU passthrough automatically with recent drivers.

## Installation Steps

1.  **Open your WSL Terminal**:
    Open "Ubuntu" (or your installed distro) from the Start menu. Do **not** use PowerShell or Command Prompt for the following steps.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/metantonio/parallel-inference-stack
    cd paralell-test
    ```

3.  **Configure Environment**:
    ```bash
    cp .env.example .env
    ```

4.  **Start the Stack**:
    ```bash
    docker-compose up -d
    ```

5.  **Verify Installation**:
    *   **Frontend**: Open [http://localhost:5173](http://localhost:5173) in your browser.
    *   **API**: [http://localhost/api/docs](http://localhost/api/docs)
    *   **Grafana**: [http://localhost:3000](http://localhost:3000) (User: `admin`, Password: `admin`)
    *   **Ray Dashboard**: [http://localhost:8265](http://localhost:8265)

## Troubleshooting

### Line Ending Issues (CRLF vs LF)
If you see errors like `exec /usr/bin/sh: no such file or directory` or scripts failing to run, it's likely due to Windows CRLF line endings.
I have included a `.gitattributes` file to handle this automatically. If you still face issues, run:
```bash
# Inside WSL
find . -type f -name "*.sh" -exec sed -i 's/\r$//' {} +
```

### GPU Not Detected
Ensure your NVIDIA drivers are up to date on Windows. You do **not** need to install CUDA drivers inside WSL; the Windows drivers propagate to WSL.
Verify GPU visibility in Docker:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Port Conflicts
If ports 80, 5173, or 3000 are already in use, you may need to modify `docker-compose.yml` to map to different host ports.
