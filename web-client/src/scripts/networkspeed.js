import { SERVER_URL } from '@/scripts/config'
export class useNetworkSpeed {
  constructor() {
    this.serverUrl = SERVER_URL;
    this.downloadSizeMB = 10; // Match your server's test size
  }

  // Test download speed (server -> client)
  async testDownload() {
    try {
      const startTime = performance.now();
      const response = await fetch(`${this.serverUrl}/api/speedtest/download`);
      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      const totalBytes = new TextEncoder().encode(JSON.stringify(data)).length;

      const endTime = performance.now();
      const durationSeconds = (endTime - startTime) / 1000;
      const speedMbps = (totalBytes * 8) / (1024 * 1024) / durationSeconds;

      return {
        speed: speedMbps,
        duration: durationSeconds,
        bytesTransferred: totalBytes
      };
    } catch (error) {
      console.error('Download test failed:', error);
      throw error;
    }
  }

  // Test upload speed (client -> server)
  async testUpload() {
    try {
      // Create test data (match server's expected size)
      const testData = '0'.repeat(this.downloadSizeMB * 1024 * 1024);
      const startTime = performance.now();
      const response = await fetch(`${this.serverUrl}/api/speedtest/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data: testData })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const result = await response.json();
      const endTime = performance.now();

      return {
        speed: result.speed_mbps,
        duration: (endTime - startTime) / 1000,
        bytesTransferred: testData.length
      };
    } catch (error) {
      console.error('Upload test failed:', error);
      throw error;
    }
  }

  // Run complete test (both upload and download)
  async runFullTest() {
    const results = {};

    console.log('Starting download test...');
    results.download = await this.testDownload();
    console.log(`Download: ${results.download.speed.toFixed(2)} Mbps`);

    console.log('Starting upload test...');
    results.upload = await this.testUpload();
    console.log(`Upload: ${results.upload.speed.toFixed(2)} Mbps`);

    return results;
  }
}