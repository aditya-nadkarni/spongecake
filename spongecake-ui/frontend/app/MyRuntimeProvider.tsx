"use client";
 
import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
 
const MyModelAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    try {
      const lastMessage = (messages[messages.length - 1]?.content[0] as { text?: string })?.text;
      const result = await fetch("http://localhost:5000/api/run-agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: lastMessage }),
        signal: abortSignal,
      });
      if (!result.ok) {
        throw new Error(`Server error: ${result.status}`);
      }
      const data = await result.json();
      
      if (!data.agent_response) {
        throw new Error("Expected agent_response to be provided");
      }

      return {
        content: [{ type: "text", text: data.agent_response || "" }],
      };
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