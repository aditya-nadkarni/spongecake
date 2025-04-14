"use client";
 
import { ReactNode, useEffect } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { API_BASE_URL } from "@/config";

// Variable to manage the event source
let eventSource: EventSource | null = null;

// Helper function to create a readable stream from an EventSource
function createEventSourceStream(url: string): ReadableStream<any> {
  return new ReadableStream({
    start(controller) {
      // Close any existing event source
      if (eventSource) {
        eventSource.close();
      }
      
      // Create a new EventSource
      eventSource = new EventSource(url);
      
      // Handle incoming messages
      if (eventSource) {
        eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          controller.enqueue(data);
          
          // If this is the completion message, close the stream
          if (data.type === 'complete') {
            controller.close();
            if (eventSource) {
              eventSource.close();
              eventSource = null;
            }
          }
        } catch (error) {
          console.error('Error parsing event data:', error);
          controller.error(error);
        }
      };
      }
      
      // Handle errors
      if (eventSource) {
        eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        controller.error(error);
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
      };
      }
    },
    cancel() {
      // Clean up the EventSource if the stream is cancelled
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    }
  });
}

const MyModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    try {
      const lastMessage = (messages[messages.length - 1]?.content[0] as { text?: string })?.text || "";
      // If last message is "ack" or "acknowledged", set safety_acknowledged to true and send to backend
      const isAck = ["ack", "acknowledged"].includes(
        lastMessage?.trim().toLowerCase() || ""
      );
      
      const result = await fetch(`${API_BASE_URL}/api/run-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: lastMessage, safety_acknowledged: isAck }),
        signal: abortSignal,
      });
      
      if (!result.ok) {
        throw new Error(`Server error: ${result.status}`);
      }
      
      const data = await result.json();
      
      // If we have a session ID, connect to the log stream
      if (data.session_id) {
        // Initial response
        yield {
          content: [{
            type: "text" as const,
            text: "Processing your request...\n"
          }],
        };
        
        // Create a stream from the EventSource
        const stream = createEventSourceStream(`${API_BASE_URL}/api/logs/${data.session_id}`);
        const reader = stream.getReader();
        
        // Collect logs
        const actionLogs: string[] = [];
        let finalResponse: string | null = null;
        let shouldStop = false;

        try {
          while (!shouldStop) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            // Process the streamed data based on type
            if (value.type === 'log') {
              const logMessage = value.message;
              
              // Extract action logs from the format "spongecake.xxx - INFO - Action: xxx"
              if (logMessage.includes(" - Action: ")) {
                // Extract the action part from the log message
                const actionPart = logMessage.split(" - Action: ")[1];
                actionLogs.push("Action: " + actionPart);
                
                // Yield updated content with filtered action logs
                yield {
                  content: [{
                    type: "text" as const,
                    text: "\n" + actionLogs.join("\n") + "\n"
                  }],
                };
              }
            } else if (value.type === 'result') {
              // Process the final response
              if (value.data) {
                try {
                  // Check for pendingSafetyCheck
                  if (value.data.pendingSafetyCheck) {
                    // Handle safety check response
                    if (value.data.agent_response && typeof value.data.agent_response === 'object' && value.data.agent_response.messages) {
                      finalResponse = value.data.agent_response.messages.join("\n") + 
                        '\n\nType "ack" to acknowledge and proceed.';
                    } else if (typeof value.data.agent_response === 'string' && value.data.agent_response.includes('pendingSafetyCheck')) {
                      try {
                        const safetyObj = JSON.parse(value.data.agent_response);
                        if (safetyObj.messages) {
                          finalResponse = safetyObj.messages.join("\n") + 
                            '\n\nType "ack" to acknowledge and proceed.';
                        } else {
                          finalResponse = 'Safety check required. Type "ack" to acknowledge and proceed.';
                        }
                      } catch (e) {
                        finalResponse = 'Safety check required. Type "ack" to acknowledge and proceed.';
                      }
                    } else {
                      finalResponse = 'Safety check required. Type "ack" to acknowledge and proceed.';
                    }
                  } 
                  // Regular agent response
                  else if (value.data.agent_response) {
                    if (typeof value.data.agent_response === 'object' && value.data.agent_response.messages) {
                      // Object with messages array
                      finalResponse = value.data.agent_response.messages.join("\n");
                    } else if (typeof value.data.agent_response === 'string') {
                      // Try to parse as JSON first
                      try {
                        const responseObj = JSON.parse(value.data.agent_response);
                        if (responseObj.messages && Array.isArray(responseObj.messages)) {
                          finalResponse = responseObj.messages.join("\n");
                        } else {
                          finalResponse = value.data.agent_response;
                        }
                      } catch (e) {
                        // Not JSON, use as is
                        finalResponse = value.data.agent_response;
                      }
                    } else {
                      finalResponse = String(value.data.agent_response);
                    }
                  }
                } catch (e) {
                  console.error("Error processing result:", e);
                  finalResponse = "Error processing response";
                }
                
                shouldStop = true;
                
                // Yield the final response, replacing previous content
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
          reader.releaseLock();
        }
      }

      // Handle safety checks and direct responses when not streaming logs
      if (!data.session_id) {
        if (!data.agent_response) {
          throw new Error("Expected agent_response to be provided");
        }

        if (data.pendingSafetyCheck || (data.agent_response && data.agent_response.includes("pendingSafetyCheck"))) {
          // If safety check, tell the user how to acknowledge the safety check and proceed
          try {
            let messages: string[] = [];
            
            // Handle different safety check formats
            if (data.pendingSafetyCheck && data.agent_response && data.agent_response.messages) {
              // Direct object with messages array
              messages = data.agent_response.messages;
            } else if (data.agent_response && typeof data.agent_response === 'string') {
              // JSON string
              const safetyCheckObject = JSON.parse(data.agent_response);
              if (safetyCheckObject.messages) {
                messages = safetyCheckObject.messages;
              }
            }
            
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
            // Fallback if parsing fails
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
          yield {
            content: [{ type: "text" as const, text: (data.agent_response || "") + "\n" }],
          };
        }
      }
    } catch (error: any) {
      if (error?.name === "AbortError") {
        console.log('User cancelled send')
        // Clean up event source if it exists
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        throw error
      } else {
        console.error("Error in run:", error);
        // Clean up event source if it exists
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        throw error;
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