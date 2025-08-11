#!/bin/bash
set -e

# Find and export the NVIDIA library paths for cuBLAS and cuDNN
# This ensures the dynamic linker can find the GPU libraries required by faster-whisper
export LD_LIBRARY_PATH=`python -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`:${LD_LIBRARY_PATH}

# Execute the command passed as arguments to this script (which will be the CMD from the Dockerfile)
exec "$@"
