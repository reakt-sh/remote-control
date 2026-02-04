
# Raspberry Pi 5 Video Capture Capability Analysis using different Camera

## Overview

This document presents the performance analysis of Raspberry Pi 5's hardware video encoding capabilities across various configurations. The tests measure CPU and GPU usage under different combinations of resolution, frame rate, and bitrate settings.

## Test Results
Camera: OmniVision ov5647


| Resolution | FPS | Bitrate | CPU Usage | GPU Usage | Notes |
|------------|-----|---------|-----------|-----------|-------|
| 640×480 | 15 | 2 Mbps | 6% | 58% | ✓ Stable |
| 640×480 | 15 | 5 Mbps | 6% | 63% | ✓ Stable |
| 640×480 | 30 | 2 Mbps | 10% | 65% | ✓ Stable |
| 640×480 | 30 | 5 Mbps | 10% | 69% | ✓ Stable |
| 640×480 | 60 | 2 Mbps | 20% | 70% | ✓ Stable |
| 640×480 | 60 | 5 Mbps | 19% | 70% | ✓ Stable |
| 1280×720 | 15 | 2 Mbps | 9% | 79% | ✓ Stable |
| 1280×720 | 15 | 5 Mbps | 9% | 81% | ✓ Stable |
| 1280×720 | 30 | 2 Mbps | 14% | 84% | ✓ Stable |
| 1280×720 | 30 | 5 Mbps | 16% | 82% | ✓ Stable |
| 1280×720 | 60 | 2 Mbps | N/A | N/A | ✗ Not Supported |
| 1920×1080 | 15 | 2 Mbps | 15% | 90% | ⚠️ Sometimes Overflow |
| 1920×1080 | 15 | 5 Mbps | 14% | 93% | ⚠️ Sometimes Overflow |
| 1920×1080 | 30 | 2 Mbps | 25% | 100% | ✗ Mostly Overflow |
| 1920×1080 | 30 | 5 Mbps | 27% | 100% | ✗ Mostly Overflow |
| 1920×1080 | 60 | 2 Mbps | N/A | N/A | ✗ Not Supported |



Camera: Dell Webcam WB3023

| Resolution | FPS (Static) | FPS (Moving) | CPU Usage | GPU Usage | Notes |
|------------|--------------|--------------|-----------|-----------|-------|
| 640×480 | 15 | 15 | 21% | 79% | ✓ Stable |
| 640×480 | 30 | 30 | 38% | 91% | ✓ Stable |
| 640×480 | 60 | - | N/A | N/A | ✗ Not Supported |
| 1280×720 | 15 | 15 | 45% | 100% | ⚠️ GPU Overflow |
| 1280×720 | 30 | 18 | 72% | 100% | ⚠️ GPU Overflow, significate frame drops |
| 1280×720 | 60 | - | N/A | N/A | ✗ Not Supported |


