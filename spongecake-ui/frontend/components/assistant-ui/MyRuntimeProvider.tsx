"use client";
 
import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { API_BASE_URL } from "@/config";
 
const MyModelAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
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

      if (!data.agent_response) {
        throw new Error("Expected agent_response to be provided");
      }

      if (data.agent_response.includes("pendingSafetyCheck")) {
        // If safety check, tell the user how to acknowledge the safety check and proceed
        const safetyCheckObject = JSON.parse(data.agent_response);
        return {
          content: [
            {
              type: "text",
              text:
                safetyCheckObject.messages.join(" ") +
                ' Type "ack" to acknowledge and proceed.',
            },
          ],
        };
      } else {
        return {
          content: [{ type: "text", text: data.agent_response || "" }],
        };
      }
    } catch (error) {
      console.error("Error in run:", error);
      throw error;
    }
  },
};

 
export function MyRuntimeProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const runtime = useLocalRuntime(MyModelAdapter);
 
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}