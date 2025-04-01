"""
Utility functions for the Spongecake backend server.
"""
import socket
import logging

logger = logging.getLogger(__name__)

class PortNotAvailableError(Exception):
    """Raised when a port is not available after multiple attempts."""
    pass

def is_port_available(port: int) -> bool:
    """Check if a port is available with proper socket configuration.
    
    Args:
        port: The port number to check
        
    Returns:
        bool: True if the port is available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.bind(("0.0.0.0", int(port)))
            # Also check if we can connect to it
            s.listen(1)
            return True
        except (OSError, socket.error):
            return False

def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port.
    
    Args:
        start_port: The port number to start checking from
        max_attempts: Maximum number of ports to check
        
    Returns:
        int: An available port number
        
    Raises:
        PortNotAvailableError: If no available port is found after max attempts
    """
    current_port = start_port
    for _ in range(max_attempts):
        if is_port_available(current_port):
            return current_port
        current_port += 1
    
    error_msg = f"Could not find an available port after {max_attempts} attempts"
    logger.error(error_msg)
    raise PortNotAvailableError(error_msg)
