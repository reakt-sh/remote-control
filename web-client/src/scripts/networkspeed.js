import { SERVER_URL } from '@/scripts/config'
export class useNetworkSpeed {
  constructor() {
    this.serverUrl = SERVER_URL;
    this.testSizeMB = 10; // Use 10MB for better accuracy
  }

  async testDownload() {
    const startTime = performance.now();
    const response = await fetch(`${this.serverUrl}/api/speedtest/download`);
    if (!response.ok) throw new Error('Download failed');
    
    // Measure actual download time
    const blob = await response.blob();
    const duration = (performance.now() - startTime) / 1000; // seconds
    const speedMbps = (blob.size * 8) / (1024 * 1024) / duration;
    
    return { speed: speedMbps, bytesTransferred: blob.size };
  }

  async testUpload() {
    // Generate realistic test data (binary, not a string)
    const testData = new Uint8Array(this.testSizeMB * 1024 * 1024).fill(0);
    const startTime = performance.now();

    const response = await fetch(`${this.serverUrl}/api/speedtest/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' }, // Send raw binary
      body: testData,
    });

    if (!response.ok) throw new Error('Upload failed');
    const duration = (performance.now() - startTime) / 1000; // seconds
    const speedMbps = (testData.length * 8) / (1024 * 1024) / duration;

    return { speed: speedMbps, bytesTransferred: testData.length };
  }

  async runFullTest() {
    console.log('Starting download test...');
    const download = await this.testDownload();
    console.log(`Download: ${download.speed.toFixed(2)} Mbps`);

    console.log('Starting upload test...');
    const upload = await this.testUpload();
    console.log(`Upload: ${upload.speed.toFixed(2)} Mbps`);

    return { download, upload };
  }
}