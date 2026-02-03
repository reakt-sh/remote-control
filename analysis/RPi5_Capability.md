
# Raspberry Pi 5 Camera Capture Capability Analysis using PiCam

## Overview

This document presents the performance analysis of Raspberry Pi 5's hardware video encoding capabilities across various configurations. The tests measure CPU and GPU usage under different combinations of resolution, frame rate, and bitrate settings.

## Test Results

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

## Key Findings

### Performance Tiers

- **640×480 (VGA)**: Excellent performance across all tested frame rates (15-60 FPS) with low resource usage
- **1280×720 (HD)**: Good performance at 15-30 FPS with moderate GPU usage (79-84%)
- **1920×1080 (Full HD)**: Limited performance; stable only at 15 FPS with occasional overflow issues

### Resource Utilization

- **CPU Usage**: Remains relatively low (6-25%) across all configurations, indicating efficient hardware encoding
- **GPU Usage**: Primary bottleneck, reaching 90-100% at higher resolutions
- **Bitrate Impact**: Minimal impact on resource usage when comparing 2 Mbps vs 5 Mbps at the same resolution/FPS

## Recommendations

1. **For Reliable Operation**: Use 1280×720 at 30 FPS or lower
2. **For Maximum Quality**: 1920×1080 at 15 FPS (monitor for overflow)
3. **For High Frame Rate**: 640×480 at 60 FPS provides smooth performance
4. **Optimal Balance**: 1280×720 at 30 FPS with 2-5 Mbps bitrate





