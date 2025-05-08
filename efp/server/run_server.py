#!/usr/bin/env python
import os
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

def start_service(service_name, command):
    """Start a service and return its process"""
    print(f"Starting {service_name}...")
    process = subprocess.Popen(
        command, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait a moment to make sure it started
    time.sleep(2)
    
    # Check if the process is still running
    if process.poll() is None:
        print(f"{service_name} started successfully!")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"Failed to start {service_name}!")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None

def main():
    """Start all backend services"""
    print("Starting Energy Consumption Forecast backend services...")
    
    # Get the API host and port from environment or use defaults
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")
    
    # Start the data collector service
    collector_process = start_service(
        "Data Collector", 
        f"cd {os.path.dirname(os.path.abspath(__file__))}/data_collector && python collector.py"
    )
    
    # Start the data processor service
    processor_process = start_service(
        "Data Processor",
        f"cd {os.path.dirname(os.path.abspath(__file__))}/data_processor && python processor.py"
    )
    
    # Start the API service
    api_process = start_service(
        "API Service",
        f"cd {os.path.dirname(os.path.abspath(__file__))}/api && python main.py"
    )
    
    if not (collector_process and processor_process and api_process):
        print("Failed to start all services. Exiting...")
        sys.exit(1)
    
    print(f"\nAll services started successfully!")
    print(f"API is running at http://{api_host}:{api_port}")
    print("Press Ctrl+C to stop all services...")
    
    try:
        # Keep the script running and monitor the processes
        while True:
            time.sleep(5)
            
            # Check if any process has exited
            for name, process in [
                ("Data Collector", collector_process),
                ("Data Processor", processor_process),
                ("API Service", api_process)
            ]:
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print(f"{name} has stopped!")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                    
                    # Restart the process
                    print(f"Attempting to restart {name}...")
                    if name == "Data Collector":
                        collector_process = start_service(
                            "Data Collector", 
                            f"cd {os.path.dirname(os.path.abspath(__file__))}/data_collector && python collector.py"
                        )
                    elif name == "Data Processor":
                        processor_process = start_service(
                            "Data Processor",
                            f"cd {os.path.dirname(os.path.abspath(__file__))}/data_processor && python processor.py"
                        )
                    elif name == "API Service":
                        api_process = start_service(
                            "API Service",
                            f"cd {os.path.dirname(os.path.abspath(__file__))}/api && python main.py"
                        )
    
    except KeyboardInterrupt:
        print("\nShutting down services...")
        
        for name, process in [
            ("Data Collector", collector_process),
            ("Data Processor", processor_process),
            ("API Service", api_process)
        ]:
            if process and process.poll() is None:
                process.terminate()
                print(f"{name} stopped.")
        
        print("All services stopped.")

if __name__ == "__main__":
    main() 