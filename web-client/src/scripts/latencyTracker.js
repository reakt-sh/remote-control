import { ref, readonly } from 'vue'

/**
 * Latency Tracker for monitoring telemetry data latency across different protocols
 */
export function useLatencyTracker() {
  // Store latency data as array of objects with sequence_number and protocol latencies
  const latencyList = ref([])

  const clockOffset = ref(0)

  // Store latency for each completed video frame
  const frameLatencies = ref([])

  // Statistics
  const stats = ref({
    websocket: { count: 0, avg: 0, min: 0, max: 0 },
    webtransport: { count: 0, avg: 0, min: 0, max: 0 },
    mqtt: { count: 0, avg: 0, min: 0, max: 0 }
  })

  function setClockOffset(newOffset) {
    clockOffset.value = newOffset
    console.log(`Clock offset updated: ${newOffset} ms`)
  }

  function recordFrameLatency(frameId, latency, createdAt = null) {
    // fix latency with clock offset
    latency += clockOffset.value
    if (latency < 0) {
      console.warn(`Negative frame latency recorded for frame ${frameId}: ${latency}ms`)
    }

    frameLatencies.value.push({
      frameId,
      latency,
      created_at: createdAt
    })
  }

  /**
   * Record latency data for a specific protocol
   * @param {string} protocol - 'websocket', 'webtransport', or 'mqtt'
   * @param {number} latency - Latency in milliseconds
   * @param {number} sequenceNumber - Sequence number from telemetry data
   */
  function recordLatency(protocol, latency, sequenceNumber, timestamp) {
    // Adjust latency with clock offset
    latency += clockOffset.value
    if (latency < 0) {
      console.warn(`Negative latency recorded for ${protocol}: ${latency}ms (seq: ${sequenceNumber})`)
    }

    // Pad protocol name for aligned output
    const paddedProtocol = protocol.padEnd(12, ' ')
    console.log(`🕒 Latency for train Telemetry: ${paddedProtocol}, ${latency}ms, seq: ${sequenceNumber}`)

    const protocolKey = getProtocolKey(protocol)
    // Find existing entry with same sequence number
    let existingEntry = latencyList.value.find(entry => entry.sequence_number === sequenceNumber)

    if (existingEntry) {
      // Update existing entry with new protocol latency
      existingEntry[protocolKey] = latency
    } else {
      // Create new entry
      const newEntry = {
        sequence_number: sequenceNumber,
        created_at: timestamp,
        ws_latency: null,
        wt_latency: null,
        mqtt_latency: null
      }
      newEntry[protocolKey] = latency
      latencyList.value.push(newEntry)
    }

    // console.log(`📊 Latency recorded for ${protocol}: ${latency}ms (seq: ${sequenceNumber})`)
  }

  /**
   * Get protocol key for the data structure
   * @param {string} protocol 
   */
  function getProtocolKey(protocol) {
    const protocolMap = {
      'websocket': 'ws_latency',
      'webtransport': 'wt_latency',
      'mqtt': 'mqtt_latency'
    }
    return protocolMap[protocol] || null
  }

  /**
   * Update statistics for all protocols
   */
  function updateStats() {
    const protocols = ['websocket', 'webtransport', 'mqtt']
    const protocolKeys = ['ws_latency', 'wt_latency', 'mqtt_latency']

    protocols.forEach((protocol, index) => {
      const protocolKey = protocolKeys[index]
      const latencies = latencyList.value
        .map(entry => entry[protocolKey])
        .filter(latency => latency !== null && latency !== undefined)

      if (latencies.length === 0) {
        stats.value[protocol] = { count: 0, avg: 0, min: 0, max: 0 }
        return
      }

      const count = latencies.length
      const sum = latencies.reduce((a, b) => a + b, 0)
      const avg = sum / count
      const min = Math.min(...latencies)
      const max = Math.max(...latencies)

      stats.value[protocol] = {
        count,
        avg: Math.round(avg * 100) / 100, // Round to 2 decimal places
        min,
        max
      }
    })
  }

  /**
   * Get latency statistics for all protocols
   */
  function getStats() {
    return { ...stats.value }
  }

  /**
   * Get all latency data for export
   */
  function getAllLatencyData() {
    // Update statistics
    updateStats()
    return {
      exportTime: new Date().toISOString(),
      statistics: getStats(),
      telemetryLatencies: [...latencyList.value],
      videoLatencies: [...frameLatencies.value],
      summary: {
        totalEntries: latencyList.value.length,
        protocols: ['websocket', 'webtransport', 'mqtt'],
        sequenceRange: getSequenceRange()
      }
    }
  }


  /**
   * Get sequence number range of collected data
   */
  function getSequenceRange() {
    if (latencyList.value.length === 0) {
      return { start: null, end: null }
    }

    const sequenceNumbers = latencyList.value.map(entry => entry.sequence_number)
    return {
      start: Math.min(...sequenceNumbers),
      end: Math.max(...sequenceNumbers)
    }
  }

  /**
   * Export latency data as JSON file
   */
  function exportToJson() {
    try {
      const data = getAllLatencyData()

      // Check if there's any data to export
      if (data.telemetryLatencies.length === 0) {
        console.warn('⚠️ No latency data to export')
        alert('No latency data available to export. Please wait for some telemetry data to be received.')
        return false
      }

      const jsonString = JSON.stringify(data, null, 2)

      // Try multiple download methods for better compatibility
      if (window.navigator && window.navigator.msSaveOrOpenBlob) {
        // For IE/Edge
        const blob = new Blob([jsonString], { type: 'application/json' })
        window.navigator.msSaveOrOpenBlob(blob, `latency-data-${new Date().toISOString().split('T')[0]}.json`)
      } else {
        // For modern browsers
        const blob = new Blob([jsonString], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)

        const link = document.createElement('a')
        link.style.display = 'none'
        link.href = url

        // just use timestamp for uniqueness
        link.download = `latency-data-${Date.now()}.json`
        link.setAttribute('download', `latency-data-${Date.now()}.json`)

        document.body.appendChild(link)

        // Force click event
        const clickEvent = new MouseEvent('click', {
          view: window,
          bubbles: true,
          cancelable: true
        })

        link.dispatchEvent(clickEvent)

        // Cleanup with delay
        setTimeout(() => {
          if (document.body.contains(link)) {
            document.body.removeChild(link)
          }
          window.URL.revokeObjectURL(url)
        }, 1000)
      }
      return true
    } catch (error) {
      console.error('❌ Failed to export latency data:', error)
      return false
    }
  }

  /**
   * Clear all latency data
   */
  function clearData() {
    latencyList.value = []
    stats.value = {
      websocket: { count: 0, avg: 0, min: 0, max: 0 },
      webtransport: { count: 0, avg: 0, min: 0, max: 0 },
      mqtt: { count: 0, avg: 0, min: 0, max: 0 }
    }
    console.log('🗑️ All latency data cleared')
  }

  /**
   * Get recent latency data (last N entries)
   * @param {number} count 
   */
  function getRecentData(count = 10) {
    return latencyList.value.slice(-count)
  }

  /**
   * Get latency data for a specific sequence number range
   * @param {number} startSeq 
   * @param {number} endSeq 
   */
  function getDataBySequenceRange(startSeq, endSeq) {
    return latencyList.value.filter(entry => 
      entry.sequence_number >= startSeq && entry.sequence_number <= endSeq
    )
  }

  /**
   * Get data for a specific sequence number
   * @param {number} sequenceNumber 
   */
  function getDataBySequenceNumber(sequenceNumber) {
    return latencyList.value.find(entry => entry.sequence_number === sequenceNumber)
  }

  return {
    // Data access
    latencyList: readonly(latencyList),
    stats,

    // Methods
    recordLatency,
    recordFrameLatency,
    getStats,
    getAllLatencyData,
    exportToJson,
    clearData,
    getRecentData,
    getDataBySequenceRange,
    getDataBySequenceNumber,
    getSequenceRange,
    setClockOffset
  }
}

// Create a global instance for the app
export const latencyTracker = useLatencyTracker()

export default latencyTracker
