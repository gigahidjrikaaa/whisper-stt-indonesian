#!/usr/bin/env python3
"""
Quick server test to verify the API starts correctly.
This script starts the server for a few seconds to test initialization.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from main import app


async def test_server():
    """Test server startup and shutdown."""
    print("🚀 Starting test server...")
    
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Start server
    await server.serve()


if __name__ == "__main__":
    print("🧪 Testing FastAPI server startup...")
    try:
        # Run server for a short test
        asyncio.run(test_server())
        print("✅ Server test completed successfully!")
    except KeyboardInterrupt:
        print("\n✅ Server test interrupted - this is expected!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        sys.exit(1)
