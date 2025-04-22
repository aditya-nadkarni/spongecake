import { LogEvent } from "./LogStreamService";

// Types for the assistant-ui content format
export type ContentType = "text";

export interface ContentItem {
  type: ContentType;
  text: string;
}

export interface AssistantResponse {
  content: ContentItem[];
}

/**
 * Parses log events into assistant UI response format
 */
export class ResponseParser {
  /**
   * Parses a log event into an assistant response
   * 
   * @param event - The log event to parse
   * @returns An assistant response with formatted content or null if no response needed
   */
  static parseLogEvent(event: LogEvent): AssistantResponse | null {
    // Skip heartbeat events
    if (event.type === "heartbeat") {
      return null;
    }
    
    // Handle log messages - only include action logs
    if (event.type === "log" && event.message) {
      // Only process logs that contain "- Action:"
      if (event.message.includes(" - Action: ")) {
        // Extract only the action part
        const actionParts = event.message.split(" - Action: ");
        if (actionParts.length > 1) {
          const actionText = "Action: " + actionParts[1];
          return {
            content: [{ type: "text", text: actionText }]
          };
        }
      }
      // Skip other log messages
      return null;
    }
    
    // Handle result data
    if (event.type === "result" && event.data) {
      // Check if this is a safety check response
      if (this.isSafetyCheckResponse(event.data)) {
        return this.parseSafetyCheckResponse(event.data);
      }
      
      // Handle agent response that might be in different formats
      return this.parseAgentResponse(event.data);
    }
    
    // Handle completion events
    if (event.type === "complete") {
      return {
        content: [{ type: "text", text: event.message || "" }]
      };
    }
    
    // For other events, we don't need to return anything
    return null;
  }
  
  /**
   * Checks if a response is a safety check
   * 
   * @param data - The response data to check
   * @returns True if this is a safety check response
   */
  static isSafetyCheckResponse(data: any): boolean {
    return (
      data.pendingSafetyCheck || 
      (data.agent_response && 
        (typeof data.agent_response === 'object' && data.agent_response[0].pendingSafetyCheck) ||
        (typeof data.agent_response === 'string' && data.agent_response.includes("pendingSafetyCheck"))
      )
    );
  }
  
  /**
   * Checks if a response is a cancellation message
   * 
   * @param data - The response data to check
   * @returns True if this is a cancellation response
   */
  static isCancellationResponse(data: any): boolean {
    // Check for various cancellation indicators
    return (
      (data.cancelled === true) ||
      (data.agent_response && typeof data.agent_response === 'string' && 
       (data.agent_response.includes('cancelled') || data.agent_response.includes('canceled'))) ||
      (data.error && typeof data.error === 'string' && 
       (data.error.includes('cancelled') || data.error.includes('canceled')))
    );
  }
  
  /**
   * Parses a safety check response
   * 
   * @param data - The safety check data
   * @returns A formatted assistant response
   */
  static parseSafetyCheckResponse(data: any): AssistantResponse {
    try {
      let messages: string[] = [];
      
      // Extract messages from different safety check formats
      if (data.agent_response && data.agent_response[0].messages && data.agent_response[0].pendingSafetyCheck) {
        // Format 1: Direct object with messages array
        messages = ["We've spotted something that might cause the agent to behave unexpectedly! Please acknowledge this to proceed.\n"]; //data.agent_response[0].messages;
      } else if (data.agent_response && typeof data.agent_response === 'string') {
        // Format 2: JSON string that needs parsing
        try {
          const safetyCheckObject = JSON.parse(data.agent_response);
          if (safetyCheckObject[0].messages) {
            messages = safetyCheckObject[0].messages;
          }
        } catch (e) {
          console.error("Error parsing safety check JSON:", e);
        }
      }
      
      // Display safety check message with instructions
      return {
        content: [
          {
            type: "text",
            text: (messages.length > 0 ? messages.join("\n") : 'Safety check required') +
                  '\n\nType "ack" to acknowledge and proceed.\n',
          },
        ],
      };
    } catch (e) {
      // Fallback message if parsing fails
      console.error("Error parsing safety check response:", e);
      return {
        content: [
          {
            type: "text",
            text: 'Safety check required. Type "ack" to acknowledge and proceed.\n',
          },
        ],
      };
    }
  }
  
  /**
   * Parses an agent response
   * 
   * @param data - The agent response data
   * @returns A formatted assistant response
   */
  static parseAgentResponse(data: any): AssistantResponse {
    try {
      let responseText = "";
      
      // Handle different response formats
      if (data.agent_response) {
        if (typeof data.agent_response === 'object') {
          // If it's an object, try to stringify it nicely
          if (data.agent_response[0].messages && Array.isArray(data.agent_response[0].messages)) {
            responseText = data.agent_response[0].messages.join("\n");
          } else {
            responseText = JSON.stringify(data.agent_response, null, 2);
          }
        } else if (typeof data.agent_response === 'string') {
          // If it's a string, try to parse it as JSON first
          try {
            const parsedResponse = JSON.parse(data.agent_response);
            if (parsedResponse.messages && Array.isArray(parsedResponse.messages)) {
              responseText = parsedResponse.messages.join("\n");
            } else {
              responseText = data.agent_response;
            }
          } catch (e) {
            // Not valid JSON, use as is
            responseText = data.agent_response;
          }
        } else {
          // Handle other types
          responseText = String(data.agent_response);
        }
      }
      
      return {
        content: [{ 
          type: "text", 
          text: responseText + "\n" 
        }]
      };
    } catch (e) {
      console.error("Error parsing agent response:", e);
      return {
        content: [{ 
          type: "text", 
          text: "Error processing response.\n" 
        }]
      };
    }
  }
  
  /**
   * Creates a cancellation response
   * 
   * @returns An assistant response for cancellation
   */
  static createCancellationResponse(): AssistantResponse {
    return {
      content: [{
        type: "text",
        text: "Request cancelled."
      }]
    };
  }
  
  /**
   * Creates an initial processing response
   * 
   * @returns An assistant response for initial processing
   */
  static createProcessingResponse(): AssistantResponse {
    return {
      content: [{
        type: "text",
        text: "Processing your request...\n"
      }]
    };
  }
}