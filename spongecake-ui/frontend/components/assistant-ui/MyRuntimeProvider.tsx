"use client";
 
import { ReactNode, useEffect } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { API_BASE_URL } from "@/config";

// Global variable to track the EventSource connection for log streaming
let eventSource: EventSource | null = null;

/**
 * Creates a ReadableStream from an EventSource connection to the backend log stream.
 * This allows us to process SSE events as a stream that can be consumed by the AsyncGenerator.
 * 
 * @param url - The URL to connect to for server-sent events
 * @returns A ReadableStream that emits parsed JSON objects from the event source
 */
function createEventSourceStream(url: string): ReadableStream<any> {
  return new ReadableStream({
    start(controller) {
      // Close any existing event source to prevent multiple connections
      if (eventSource) {
        eventSource.close();
      }
      
      // Create a new EventSource connection to the server
      eventSource = new EventSource(url);
      
      // Set up event handler for incoming messages
      if (eventSource) {
        eventSource.onmessage = (event) => {
        try {
          console.log(event.data) // Debug: log raw event data
          
          // Parse the JSON data from the event
          const data = JSON.parse(event.data);
          
          // Add the parsed data to the stream
          controller.enqueue(data);
          
          // If this is the completion message, close the stream and clean up
          if (data.type === 'complete') {
            controller.close();
            if (eventSource) {
              eventSource.close();
              eventSource = null;
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
      if (eventSource) {
        eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        controller.error(error);
        
        // Clean up on error
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
      };
      }
    },
    // Clean up function called when the stream is cancelled
    cancel() {
      // Ensure the EventSource is properly closed
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    }
  });
}

/**
 * The ChatModelAdapter implementation for the Spongecake SDK.
 * This adapter handles communication with the backend API and processes streaming logs.
 */
const MyModelAdapter: ChatModelAdapter = {
  /**
   * Main run function that processes user messages and streams responses.
   * Implemented as an AsyncGenerator to support streaming responses.
   */
  async *run({ messages, abortSignal }) {
    try {
      // Extract the last message from the user
      const lastMessage = (messages[messages.length - 1]?.content[0] as { text?: string })?.text || "";
      
      // Check if this is an acknowledgment for a safety check
      // If the user types "ack" or "acknowledged", we'll pass that to the backend
      const isAck = ["ack", "acknowledged", "y", "yes"].includes(
        lastMessage?.trim().toLowerCase() || ""
      );
      
      // Send initial call to start an agent action
      const result = await fetch(`${API_BASE_URL}/api/run-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: lastMessage, safety_acknowledged: isAck }),
        signal: abortSignal, // Support for cancellation
      });
      
      // Handle HTTP errors
      if (!result.ok) {
        throw new Error(`Server error: ${result.status}`);
      }
      
      // Parse the initial response
      const data = await result.json();
      
      /*
       * Stream logs from the backend to the frontend to track what the agent is doing
       */
      if (data.session_id) {
        // Show initial "Processing" message while waiting for logs
        yield {
          content: [{
            type: "text" as const,
            text: "Processing your request...\n"
          }],
        };
        
        // Connect to the log stream endpoint to see what the agent is doing (using SSE)
        const stream = createEventSourceStream(`${API_BASE_URL}/api/logs/${data.session_id}`);
        const reader = stream.getReader();
        
        // State variables to track streaming progress
        const actionLogs: string[] = []; // Store filtered action logs
        let finalResponse: string | null = null; // Store the final agent response
        let shouldStop = false; // Flag to control the streaming loop

        try {
          // Main streaming loop - continues until shouldStop is true
          while (!shouldStop) {
            const { done, value } = await reader.read();
            
            // Exit if the stream is done
            if (done) break;
            
            // Process different message types from the backend
            // Process an agent action log
            if (value.type === 'log') {
              const logMessage = value.message;
              
              // Filter logs to only show logs that reference an agent action
              if (logMessage.includes(" - Action: ")) {
                const actionPart = logMessage.split(" - Action: ")[1];
                actionLogs.push("Action: " + actionPart);
                
                // Update the chat with the action taken
                yield {
                  content: [{
                    type: "text" as const,
                    text: "\n" + actionLogs.join("\n") + "\n"
                  }],
                };
              }
            }
            // Process a result message - either when the agent needs further input, safety check acknowledgment, or a task complete response
            else if (value.type === 'result') {
              if (value.data) {
                try {
                  // Agent response can either be an object or a single string
                  if (typeof value.data.agent_response === 'object' && value.data.agent_response.messages) {
                    finalResponse = value.data.agent_response.messages.join("\n");
                  } else if (typeof value.data.agent_response === 'string') {
                    try {
                      const responseObj = JSON.parse(value.data.agent_response);
                      if (responseObj.messages && Array.isArray(responseObj.messages)) {
                        // Extract and join messages from parsed JSON
                        finalResponse = responseObj.messages.join("\n");
                      } else {
                        // Use the raw string if no messages array
                        finalResponse = value.data.agent_response;
                      }
                    } catch (e) {
                      // Not valid JSON, use the string as is
                      finalResponse = value.data.agent_response;
                    }
                  } else {
                    // Handle non-string, non-object responses
                    finalResponse = String(value.data.agent_response);
                  }
                } catch (e) {
                  // Log and handle any errors in processing the result
                  console.error("Error processing result:", e);
                  finalResponse = "Error processing response";
                }
                
                // Set flag to stop the streaming loop
                shouldStop = true;
                
                // Yield the final response, which replaces all previous content
                // This is the message that will remain in the chat after processing
                yield {
                  content: [{
                    type: "text" as const,
                    text: finalResponse + "\n"
                  }],
                };
              }
            }
          }
        } finally {
          // Release the reader lock to prevent memory leaks
          reader.releaseLock();
        }
      }

      // Handle direct responses (non-streaming mode)
      // This path is taken when the backend doesn't provide a session_id for streaming
      if (!data.session_id) {
        // Validate that we have a response
        if (!data.agent_response) {
          throw new Error("Expected agent_response to be provided");
        }

        // Handle safety check responses
        if (data.pendingSafetyCheck || (data.agent_response && data.agent_response.includes("pendingSafetyCheck"))) {
          try {
            let messages: string[] = [];
            
            // Extract messages from different safety check formats
            if (data.pendingSafetyCheck && data.agent_response && data.agent_response.messages) {
              // Format 1: Direct object with messages array
              messages = data.agent_response.messages;
            } else if (data.agent_response && typeof data.agent_response === 'string') {
              // Format 2: JSON string that needs parsing
              const safetyCheckObject = JSON.parse(data.agent_response);
              if (safetyCheckObject.messages) {
                messages = safetyCheckObject.messages;
              }
            }
            
            // Display safety check message with instructions
            yield {
              content: [
                {
                  type: "text" as const,
                  text:
                    (messages.length > 0 ? messages.join("\n") : 'Safety check required') +
                    '\n\nType "ack" to acknowledge and proceed.\n',
                },
              ],
            };
          } catch (e) {
            // Fallback message if parsing fails
            yield {
              content: [
                {
                  type: "text" as const,
                  text: 'Safety check required. Type "ack" to acknowledge and proceed.\n',
                },
              ],
            };
          }
        } else {
          // Regular direct response (non-safety check)
          yield {
            content: [{ type: "text" as const, text: (data.agent_response || "") + "\n" }],
          };
        }
      }
    } catch (error: any) {
      // Handle user cancellation (abort) separately from other errors
      if (error?.name === "AbortError") {
        console.log('User cancelled send')
        // Clean up resources when request is cancelled
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        throw error // Re-throw to let the UI handle cancellation
      } else {
        // Handle all other errors
        console.error("Error in run:", error);
        // Ensure EventSource is cleaned up on error
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        throw error; // Re-throw to let the UI show error state
      }
    }
  },
};



export function MyRuntimeProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const runtime = useLocalRuntime(MyModelAdapter);
  
  // Clean up event source on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };
  }, []);
 
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}