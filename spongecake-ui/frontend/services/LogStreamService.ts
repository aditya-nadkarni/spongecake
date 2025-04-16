import { API_BASE_URL } from "@/config";

// Event types returned from the server
export type LogEventType = "log" | "result" | "complete" | "heartbeat";

// Parsed event data structure
export interface LogEvent {
  type: LogEventType;
  message?: string;
  data?: any;
}

// Global variable to track the EventSource connection
let activeEventSource: EventSource | null = null;

/**
 * Creates a stream from an EventSource connection to the backend log stream.
 * 
 * @param sessionId - The session ID to connect to
 * @returns A ReadableStream that emits parsed LogEvent objects
 */
export function createLogStream(sessionId: string): ReadableStream<LogEvent> {
  // Create the URL for the log stream
  const logStreamUrl = `${API_BASE_URL}/api/logs/${sessionId}`;
  console.log(`Creating log stream for session ${sessionId} at ${logStreamUrl}`);
  
  return new ReadableStream<LogEvent>({
    start(controller) {
      // Close any existing event source to prevent multiple connections
      if (activeEventSource) {
        activeEventSource.close();
      }
      
      // Create a new EventSource connection to the server
      activeEventSource = new EventSource(logStreamUrl);
      
      // Set up event handler for incoming messages
      if (activeEventSource) {
        activeEventSource.onmessage = (event) => {
          try {
            console.log('Raw event data:', event.data);
            
            // Parse the JSON data from the event
            const parsedData = JSON.parse(event.data);
            
            // Add the parsed data to the stream
            controller.enqueue(parsedData);
            
            // If this is the completion message, close the stream and clean up
            if (parsedData.type === 'complete') {
              controller.close();
              if (activeEventSource) {
                activeEventSource.close();
                activeEventSource = null;
              }
            }
          } catch (error) {
            // Handle JSON parsing errors
            console.error('Error parsing event data:', error);
            controller.error(error);
          }
        };
      }
      
      // Set up error handler for the EventSource
      if (activeEventSource) {
        activeEventSource.onerror = (error) => {
          console.error('EventSource error:', error);
          controller.error(error);
          
          // Clean up on error
          if (activeEventSource) {
            activeEventSource.close();
            activeEventSource = null;
          }
        };
      }
    },
    
    // Clean up function called when the stream is cancelled
    cancel() {
      // Ensure the EventSource is properly closed
      if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
      }
    }
  });
}

/**
 * Cancels an active log stream session
 * 
 * @param sessionId - The session ID to cancel
 * @returns Promise that resolves when cancellation is complete
 */
export async function cancelLogStream(sessionId: string): Promise<void> {
  if (!sessionId) {
    console.error('No session ID provided for cancellation');
    return;
  }
  
  console.log(`Sending cancellation request for session ${sessionId}`);
  
  try {
    // Call the backend cancellation endpoint
    const response = await fetch(`${API_BASE_URL}/api/cancel-agent/${sessionId}`, {
      method: 'POST',
    });
    
    // Close the active event source
    if (activeEventSource) {
      activeEventSource.close();
      activeEventSource = null;
    }
    
    console.log('Cancellation response:', await response.json());
  } catch (error) {
    console.error('Error sending cancellation request:', error);
  }
}