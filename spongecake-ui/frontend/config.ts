/**
 * Frontend configuration settings
 */

// Backend API configuration
export const API_CONFIG = {
  // The host and port where the backend server is running
  // Default: localhost:5001
  HOST: 'localhost',
  PORT: 5000,
};

// Backend API base URL (constructed once)
export const API_BASE_URL = `http://${API_CONFIG.HOST}:${API_CONFIG.PORT}`;

// VNC viewer configuration
export const VNC_CONFIG = {
  // The host for VNC connections
  // This is typically the same as the API host for local development
  VNC_HOST: 'localhost',
  
  // The default VNC password
  PASSWORD: 'secret',
  
  // Whether to auto-connect
  AUTO_CONNECT: true,
};

/**
 * Constructs a VNC viewer URL with the given port
 */
export function getVncUrl(port: number): string {
  return `http://${API_CONFIG.HOST}:${port}/vnc.html?host=${VNC_CONFIG.VNC_HOST}&port=5900&password=${VNC_CONFIG.PASSWORD}&autoconnect=${VNC_CONFIG.AUTO_CONNECT}`;
}
