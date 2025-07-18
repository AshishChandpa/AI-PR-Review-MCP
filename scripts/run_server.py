#!/usr/bin/env python3
import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_mcp_server():
    """Run the MCP server in the background"""
    cmd = [sys.executable, str(project_root / "src" / "mcp_server.py")]
    try:
        return subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Failed to start MCP server: {e}")
        return None


def run_ui_server():
    """Run the UI server"""
    cmd = [sys.executable, str(project_root / "ui" / "app.py")]
    try:
        print("Starting UI server...")
        print(subprocess.check_output(cmd))
        return subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Failed to start UI server: {e}")

        return None


async def main():
    print("🚀 Starting PR Review MCP Server...")

    processes = []

    # Start UI server first (more stable)
    ui_process = run_ui_server()
    if ui_process:
        processes.append(ui_process)
        print("✅ UI Server started at http://localhost:8080")
        time.sleep(2)  # Give UI server time to start
    else:
        print("❌ Failed to start UI Server")
        return

    # Start MCP server
    mcp_process = run_mcp_server()
    if mcp_process:
        processes.append(mcp_process)
        print("✅ MCP Server started (stdio mode)")
        time.sleep(1)  # Give MCP server time to start
    else:
        print("❌ Failed to start MCP Server")
        # UI server can still work without MCP
        print("📝 UI Server is still running at http://localhost:8080")

    print("\n🎉 Server Status:")
    print("   • UI Server: http://localhost:8080")
    print("   • MCP Server: Running in stdio mode")
    print("\n🔧 You can now:")
    print("   • Use the web UI at http://localhost:8080")
    print("   • Configure MCP in VS Code/Cursor")
    print("\n⏹️  Press Ctrl+C to stop all servers")

    try:
        # Monitor processes
        while True:
            for process in processes:
                if process.poll() is not None:
                    print(f"⚠️  Process {process.pid} exited")
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ All servers stopped")


if __name__ == "__main__":
    asyncio.run(main())
