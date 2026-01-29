import subprocess
import sys
import os
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='framework_monitor_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_monitor():
    while True:
        try:
            # Get the Django project directory
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Change to the project directory
            os.chdir(project_dir)
            
            logging.info('Starting framework monitor process...')
            
            # Run the management command
            process = subprocess.Popen(
                [sys.executable, 'manage.py', 'monitor_frameworks'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            # Log the process start
            logging.info(f'Framework monitor started with PID: {process.pid}')
            
            # Monitor the process
            while True:
                # Read output with timeout
                output = process.stdout.readline()
                if output:
                    logging.info(output.strip())
                
                error = process.stderr.readline()
                if error:
                    logging.error(error.strip())
                
                # Check if process is still running
                if process.poll() is not None:
                    logging.error('Framework monitor process died unexpectedly')
                    break
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.1)
            
            # If we get here, the process died
            logging.error('Framework monitor process died, restarting in 5 seconds...')
            time.sleep(5)  # Wait 5 seconds before restarting
                
        except Exception as e:
            logging.error(f'Error running framework monitor: {str(e)}')
            logging.info('Restarting in 5 seconds...')
            time.sleep(5)  # Wait 5 seconds before retrying

if __name__ == '__main__':
    try:
        logging.info('Framework monitor service starting...')
        run_monitor()
    except KeyboardInterrupt:
        logging.info('Framework monitor service stopped by user.')
    except Exception as e:
        logging.error(f'Fatal error in framework monitor service: {str(e)}')
        sys.exit(1) 