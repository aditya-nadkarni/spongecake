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

      const lastMessage = messages[messages.length - 1]?.content[0]?.text;

      console.log('Sending these messages to the backend', lastMessage)
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
      
      // Use the logs property from the data
      if (!data.logs || !Array.isArray(data.logs)) {
        throw new Error("Expected data.logs to be an array");
      }

      return {
        content: data.logs.map((message: any) => ({
          type: "text",
          text: message?.content[0]?.text,
        })),
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