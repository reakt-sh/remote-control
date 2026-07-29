import { ref } from 'vue'

/**
 * Composable that owns all per-camera frame state and the frame-complete handler.
 *
 * @param {Object} deps - Shared reactive refs from trainStore
 * @param {import('vue').Ref} deps.averageClockOffset
 * @param {import('vue').Ref} deps.indexedDBStorageEnabled
 * @param {Object}            deps.dataStorage
 * @param {import('vue').Ref} deps.selectedTrainId
 */
export function useVideoFrameHandler({ averageClockOffset, indexedDBStorageEnabled, dataStorage, selectedTrainId }) {

  // Per-camera frame references (consumed by video renderer components)
  const frameRefFront = ref(null)
  const frameRefRear = ref(null)

  // Toggle per-frame latency recording for analysis
  const enableStatistics = ref(true)

  // Per-camera latency tracking (last 30 frames)
  const last30_latencyHistory_front = ref([])
  const last30_framesAverageLatency_front = ref(0)
  const last30_latencyHistory_rear = ref([])
  const last30_framesAverageLatency_rear = ref(0)

  // Per-camera FPS tracking (last 1 second)
  const last1s_frameTimestamps_front = ref([])
  const last1s_framesFPS_front = ref(0)
  const last1s_frameTimestamps_rear = ref([])
  const last1s_framesFPS_rear = ref(0)

  // Per-camera bandwidth tracking (last 1 second)
  const last1s_bytesHistory_front = ref([])
  const last1s_bandwidthMbps_front = ref(0)
  const last1s_bytesHistory_rear = ref([])
  const last1s_bandwidthMbps_rear = ref(0)

  // Per-camera frame-latency analysis (last 100 frames)
  const last_100_frame_latencies_front = ref([])
  const last_frame_id_completed_front = ref(0)
  const last_100_frame_latencies_rear = ref([])
  const last_frame_id_completed_rear = ref(0)

  /**
   * Called by each camera's assembler when a frame is fully assembled.
   * Routes all metrics updates to the correct per-camera reactive refs.
   */
  function handleFrameComplete(completedFrame) {
    const cameraId = completedFrame.cameraId
    const isFront = cameraId === 'front'

    // Calculate latency with clock offset
    const frameLatency = completedFrame.latency + averageClockOffset.value

    // Drop frames with excessive latency
    if (frameLatency > 1000) {
      console.warn(`⚠️ Frame ${completedFrame.frameId} [${cameraId}] skipped - latency too high: ${frameLatency.toFixed(0)} ms`)
      return
    }

    // Select per-camera reactive refs
    const frameRef          = isFront ? frameRefFront                    : frameRefRear
    const latencyHistory    = isFront ? last30_latencyHistory_front      : last30_latencyHistory_rear
    const avgLatencyRef     = isFront ? last30_framesAverageLatency_front : last30_framesAverageLatency_rear
    const frameTimestamps   = isFront ? last1s_frameTimestamps_front     : last1s_frameTimestamps_rear
    const framesFPSRef      = isFront ? last1s_framesFPS_front           : last1s_framesFPS_rear
    const bytesHistory      = isFront ? last1s_bytesHistory_front        : last1s_bytesHistory_rear
    const bandwidthRef      = isFront ? last1s_bandwidthMbps_front       : last1s_bandwidthMbps_rear
    const frameLatenciesRef = isFront ? last_100_frame_latencies_front   : last_100_frame_latencies_rear
    const lastFrameIdRef    = isFront ? last_frame_id_completed_front    : last_frame_id_completed_rear

    frameRef.value = completedFrame.data

    if (indexedDBStorageEnabled.value) {
      dataStorage.storeFrame({
        frameId: completedFrame.frameId,
        data: completedFrame.data,
        trainId: selectedTrainId.value,
        createdAt: completedFrame.created_at,
        receivedAt: completedFrame.received_at,
        latency: frameLatency,
        cameraId: cameraId,
      })
    }

    if(enableStatistics.value) {
      // Average latency of last 30 frames
      if (latencyHistory.value.length >= 30) {
        latencyHistory.value.shift()
      }
      latencyHistory.value.push(frameLatency)
      avgLatencyRef.value = latencyHistory.value.reduce((a, b) => a + b, 0) / latencyHistory.value.length

      // FPS over the last 1 second
      const currentTime = performance.now()
      frameTimestamps.value.push(currentTime)
      while (frameTimestamps.value.length > 0 && currentTime - frameTimestamps.value[0] > 1000) {
        frameTimestamps.value.shift()
      }
      framesFPSRef.value = frameTimestamps.value.length

      // Bandwidth over the last 1 second
      bytesHistory.value.push({ timestamp: currentTime, size: completedFrame.data.length })
      while (bytesHistory.value.length > 0 && currentTime - bytesHistory.value[0].timestamp > 1000) {
        bytesHistory.value.shift()
      }
      bandwidthRef.value = (bytesHistory.value.reduce((sum, e) => sum + e.size, 0) * 8) / (1024 * 1024)
   }

    // Per-frame latency history (last 100) for analysis
    if (enableStatistics.value) {
      if (lastFrameIdRef.value === 0 || completedFrame.frameId === lastFrameIdRef.value + 1) {
        frameLatenciesRef.value.push({ frameId: completedFrame.frameId, latency: frameLatency })
        if (frameLatenciesRef.value.length > 100) frameLatenciesRef.value.shift()
      } else {
        for (let missingId = lastFrameIdRef.value + 1; missingId < completedFrame.frameId; missingId++) {
          frameLatenciesRef.value.push({ frameId: missingId, latency: null })
          if (frameLatenciesRef.value.length > 100) frameLatenciesRef.value.shift()
        }
        frameLatenciesRef.value.push({ frameId: completedFrame.frameId, latency: frameLatency })
        if (frameLatenciesRef.value.length > 100) frameLatenciesRef.value.shift()
      }
    }

    lastFrameIdRef.value = completedFrame.frameId
  }

  return {
    frameRefFront,
    frameRefRear,
    last30_framesAverageLatency_front,
    last30_framesAverageLatency_rear,
    last1s_framesFPS_front,
    last1s_framesFPS_rear,
    last1s_bandwidthMbps_front,
    last1s_bandwidthMbps_rear,
    last_100_frame_latencies_front,
    last_100_frame_latencies_rear,
    handleFrameComplete,
  }
}
