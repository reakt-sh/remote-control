import subprocess
import json
import statistics
from typing import Dict, Optional, Tuple, List
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from loguru import logger
from globals import SERVER
import asyncio
import re

class NetworkSpeed(QThread):
    speed_calculated = pyqtSignal(object)
    
    def __init__(self, server_host: str = SERVER, port: int = 5201, duration: int = 10, ping_count: int = 10):
        super().__init__()
        self.server_host = server_host
        self.port = port
        self.duration = duration
        self.ping_count = ping_count
        self.loop = asyncio.new_event_loop()
        logger.debug(f"NetworkSpeedTester initialized for server {server_host}:{port}")

    def _run_iperf_test(self, reverse: bool = False) -> Optional[Dict]:
        cmd = [
            "iperf3",
            "-c", self.server_host,
            "-p", str(self.port),
            "-t", str(self.duration),
            "-J",
            "--forceflush",
        ]
        if reverse:
            cmd.append("-R")

        try:
            logger.info(f"Starting iperf3 test: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"iperf3 test failed: {e.stderr.strip()}")
        except json.JSONDecodeError:
            logger.error("Failed to parse iperf3 JSON output")
        except Exception as e:
            logger.error(f"Unexpected error during iperf3 test: {str(e)}")
        return None

    def _run_ping_test(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Run ping test to measure latency and jitter
        Returns: (average_ping, jitter)
        """
        cmd = [
            "ping",
            "-c", str(self.ping_count),
            "-i", "0.2",  # 200ms interval between pings
            self.server_host
        ]
        
        try:
            logger.info(f"Starting ping test: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return self._parse_ping_output(result.stdout)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Ping test failed: {e.stderr.strip()}")
        except Exception as e:
            logger.error(f"Unexpected error during ping test: {str(e)}")
        
        return None, None

    def _parse_ping_output(self, output: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse ping output to extract average latency and calculate jitter
        Returns: (average_ping, jitter)
        """
        try:
            # Extract individual ping times
            ping_times = []
            time_pattern = r'time=(\d+\.?\d*)'
            
            for line in output.split('\n'):
                match = re.search(time_pattern, line)
                if match:
                    ping_times.append(float(match.group(1)))
            
            if not ping_times:
                logger.warning("No ping times found in output")
                return None, None
            
            # Calculate average ping
            avg_ping = statistics.mean(ping_times)
            
            # Calculate jitter (standard deviation of ping times)
            if len(ping_times) > 1:
                jitter = statistics.stdev(ping_times)
            else:
                jitter = 0.0
            
            logger.info(f"Ping analysis: avg={avg_ping:.2f}ms, jitter={jitter:.2f}ms, samples={len(ping_times)}")
            return round(avg_ping, 2), round(jitter, 2)
            
        except Exception as e:
            logger.error(f"Error parsing ping output: {str(e)}")
            return None, None

    def _run_alternative_ping_test(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Alternative ping implementation using fping for more detailed jitter calculation
        Only use if fping is available on the system
        """
        cmd = [
            "fping",
            "-c", str(self.ping_count),
            "-p", "200",  # 200ms interval
            "-q",  # Quiet output
            self.server_host
        ]
        
        try:
            logger.info(f"Starting fping test: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # fping outputs to stderr by default
            output = result.stderr
            
            # Parse fping output: "host : xmt/rcv/%loss = 10/10/0%, min/avg/max = 1.23/2.34/3.45"
            stats_pattern = r'min/avg/max = ([\d.]+)/([\d.]+)/([\d.]+)'
            match = re.search(stats_pattern, output)
            
            if match:
                min_time = float(match.group(1))
                avg_time = float(match.group(2))
                max_time = float(match.group(3))
                
                # Estimate jitter as (max - min) / 2
                jitter = (max_time - min_time) / 2
                
                logger.info(f"fping analysis: avg={avg_time:.2f}ms, jitter={jitter:.2f}ms")
                return round(avg_time, 2), round(jitter, 2)
            
        except FileNotFoundError:
            logger.debug("fping not available, falling back to regular ping")
        except Exception as e:
            logger.error(f"Error with fping test: {str(e)}")
        
        return None, None

    def run(self):
        self.measure_speeds()

    def measure_speeds(self):
        """Enhanced speed test including ping and jitter measurements"""
        logger.info("Starting comprehensive network measurements...")
        
        # Run ping test first (usually faster)
        logger.info("Measuring latency and jitter...")
        ping, jitter = self._run_ping_test()
        
        # Try alternative ping method if regular ping failed
        if ping is None or jitter is None:
            ping, jitter = self._run_alternative_ping_test()
        
        # Run iperf3 tests for bandwidth
        logger.info("Measuring download speed...")
        download = self._run_iperf_test(reverse=True)
        
        logger.info("Measuring upload speed...")
        upload = self._run_iperf_test(reverse=False)
        
        # Extract speeds
        download_speed = download['end']['sum_received']['bits_per_second'] / 1e6 if download else None
        upload_speed = upload['end']['sum_sent']['bits_per_second'] / 1e6 if upload else None
        
        # Compile results
        data = {
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "ping": ping,
            "jitter": jitter,
            "timestamp": self._get_timestamp()
        }
        
        logger.info(f"Network measurements complete: {data}")
        self.speed_calculated.emit(data)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required network tools are available"""
        tools = {
            "iperf3": False,
            "ping": False,
            "fping": False
        }
        
        for tool in tools.keys():
            try:
                subprocess.run([tool, "--help"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
                tools[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                tools[tool] = False
        
        logger.info(f"Network tools availability: {tools}")
        return tools
