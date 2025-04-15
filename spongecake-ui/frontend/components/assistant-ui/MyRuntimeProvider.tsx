"use client";

import { ReactNode, useEffect } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

// Import services
import { AgentService } from "@/services/AgentService";
import { createLogStream, cancelLogStream } from "@/services/LogStreamService";
import { ResponseParser } from "@/services/ResponseParser";

// Import session context
import { useSession } from "./SessionContext";

// Create a global variable for session ID access from components
// This makes it easier to pass the session ID around without complex typing
type SessionManager = {
  setSessionId: (id: string | null) => void;
  getSessionId: () => string | null;
};

export const sessionManager: SessionManager = {
  setSessionId: (id: string | null) => {
    console.log(`Global session manager: Setting ID to ${id}`);
    // Update in window for backwards compatibility
    if (typeof window !== 'undefined') {
      (window as any).currentSessionId = id;
    }
  },
  getSessionId: () => {
    // Read from window for backwards compatibility
    if (typeof window !== 'undefined') {
      return (window as any).currentSessionId || null;
    }
    return null;
  }
};

/**
 * The ChatModelAdapter implementation for the Spongecake SDK.
 * This adapter handles communication with the backend API and processes streaming logs.
 */
const MyModelAdapter: ChatModelAdapter = {
  /**
   * Main run function that processes user messages and streams responses.
   * Implemented as an AsyncGenerator to support streaming responses.
   */
  async *run(options: { messages: any; abortSignal?: AbortSignal }) {
    try {
      // Extract options
      const { messages, abortSignal } = options;
      
      // Set up abort listener for debugging
      if (abortSignal) {
        abortSignal.addEventListener('abort', () => {
          console.log('Abort signal triggered!', new Date().toISOString());
        });
      }
      
      // Extract the last message from the user
      const lastMessage = (messages[messages.length - 1]?.content[0] as { text?: string })?.text || "";
      
      // Check if this is an acknowledgment for a safety check
      const isAck = ["ack", "acknowledged", "y", "yes"].includes(
        lastMessage?.trim().toLowerCase() || ""
      );
      
      // Send initial call to start an agent action
      const data = await AgentService.runAgent({
        messages: lastMessage,
        safetyAcknowledged: isAck,
        abortSignal
      });
      
      // If we have a session ID, store it in our session manager
      if (data.session_id) {
        console.log(`Setting session ID: ${data.session_id}`);
        sessionManager.setSessionId(data.session_id);
      }
      
      // Handle direct responses (no session ID)
      if (!data.session_id) {
        // Check for errors
        if (data.error) {
          throw new Error(data.error);
        }
        
        // Let ResponseParser handle all the parsing logic
        if (ResponseParser.isSafetyCheckResponse(data)) {
          yield ResponseParser.parseSafetyCheckResponse(data);
        } else {
          yield ResponseParser.parseAgentResponse(data);
        }
        return;
      }
      
      // Show initial "Processing" message while waiting for logs
      yield ResponseParser.createProcessingResponse();
      
      // Create a stream from the server-sent events
      const stream = createLogStream(data.session_id);
      const reader = stream.getReader();
      
      // Process the stream
      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          // Parse the log event
          const response = ResponseParser.parseLogEvent(value);
          if (response) yield response;
          
          // If this is a completion message, break the loop
          if (value.type === 'complete' || value.type === 'result') break;
        }
      } finally {
        // Make sure to release the reader
        reader.releaseLock();
      }
    } catch (error: any) {
      // Handle user cancellation (abort) separately from other errors
      if (error?.name === "AbortError") {
        console.log('User cancelled request via AbortError', error);
        
        try {
          // Get the session ID from our manager
          const sessionId = sessionManager.getSessionId();
          if (sessionId) {
            console.log(`Cancelling session: ${sessionId}`);
            await cancelLogStream(sessionId);
          } else {
            console.warn('No active session ID found for cancellation');
          }
        } catch (cancelError) {
          console.error('Error during cancellation:', cancelError);
        }
        
        // Show cancellation message instead of error
        yield ResponseParser.createCancellationResponse();
        return;
      }
      // Handle all other errors
      console.error("Error in run:", error);
      throw error; // Re-throw to let the UI show error state
    }
  },
};

/**
 * MyRuntimeProvider component that provides the runtime to the assistant UI.
 */
export function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const runtime = useLocalRuntime(MyModelAdapter);
  const { setSessionId } = useSession();
  
  // Sync our session manager with the context
  useEffect(() => {
    // Override the setSessionId method to update the context as well
    const originalSetSessionId = sessionManager.setSessionId;
    sessionManager.setSessionId = (id: string | null) => {
      // Call the original function to update window
      originalSetSessionId(id);
      // Also update the context
      setSessionId(id);
    };
    
    // Clean up when component unmounts
    return () => {
      sessionManager.setSessionId(null);
    };
  }, [setSessionId]);
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}