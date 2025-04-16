import { API_BASE_URL } from "@/config";

/**
 * Interface for agent request options
 */
export interface AgentRequestOptions {
  messages: string;
  safetyAcknowledged?: boolean;
  autoMode?: boolean;
  abortSignal?: AbortSignal;
}

/**
 * Interface for agent response
 */
export interface AgentResponse {
  session_id?: string;
  novncPort?: number;
  agent_response?: string | any;
  pendingSafetyCheck?: boolean;
  error?: string;
}

/**
 * Service for communicating with the agent backend
 */
export class AgentService {
  /**
   * Sends a request to run the agent with the given messages
   * 
   * @param options - The request options
   * @returns A promise that resolves to the agent response
   */
  static async runAgent(options: AgentRequestOptions): Promise<AgentResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/run-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: options.messages,
          safety_acknowledged: options.safetyAcknowledged || false,
          auto_mode: options.autoMode || false
        }),
        signal: options.abortSignal
      });
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error: any) {
      // Rethrow AbortError to be handled by the caller
      if (error.name === "AbortError") {
        throw error;
      }
      
      // Handle other errors
      console.error("Error running agent:", error);
      return {
        error: error.message || "Unknown error occurred"
      };
    }
  }
}