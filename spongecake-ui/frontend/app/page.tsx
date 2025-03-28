"use client";

import React, { useState } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import { ThreadList } from "@/components/assistant-ui/thread-list";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { AssistantRuntimeProvider } from "@assistant-ui/react";

export default function Home() {
  // Set up the assistant chat runtime (which calls your /api/chat endpoint)
  const runtime = useChatRuntime({ api: "/api/chat" });

  // State for the desktop agent (container/VNC) controls
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const [agentDone, setAgentDone] = useState(false);
  const [userPrompt, setUserPrompt] = useState("");
  const [autoMode, setAutoMode] = useState(true);


  // Function to start the container (and noVNC)
  const handleStartContainer = async () => {
    try {
      const resp = await fetch("http://localhost:5000/api/start-container", {
        method: "POST",
      });
      const data = await resp.json();
      console.log("Container logs:", data.logs);
      setLogs(data.logs || []);
      setContainerStarted(true);
    } catch (error) {
      console.error("Error starting container:", error);
    }
  };

  // Function to show the VNC viewer iframe
  const handleOpenVNC = () => {
    setVncShown(true);
  };

  const handleRunAgent = async () => {
    try {
      const resp = await fetch("http://localhost:5000/api/run-agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userPrompt, autoMode }),
      });
      const data = await resp.json();
      console.log("Agent logs:", data.logs);
      setLogs(data.logs || []);
      setAgentDone(true);
    } catch (error) {
      console.error("Error running agent:", error);
    }
  };

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <main className="px-4 py-4">
        <h1 className="text-2xl font-bold mb-4">Desktop Agent UI with Chat Assistant</h1>
        <div className="grid grid-cols-3 gap-4">
          {/* LEFT SIDEBAR: Desktop Agent Controls */}
          <div className="col-span-1 space-y-4">
            {/* Auto-mode Checkbox */}
          <div style={{ marginTop: "8px" }}>
            <input
              type="checkbox"
              checked={autoMode}
              onChange={() => setAutoMode(!autoMode)}
            />
            <label style={{ marginLeft: "4px" }}>Auto mode</label>
          </div>

            {!containerStarted ? (
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded"
                onClick={handleStartContainer}
              >
                Start Desktop + noVNC
              </button>
            ) : (
              <div className="text-green-600 font-semibold">
                Container + noVNC are started!
              </div>
            )}

            {containerStarted && !vncShown && (
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded"
                onClick={handleOpenVNC}
              >
                Open VNC Viewer
              </button>
            )}

            {logs.length > 0 && (
              <div>
                <h3 className="font-bold">Logs:</h3>
                <div className="text-sm">
                  {logs.map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Interface */}
            <div className="border rounded p-2 h-[400px]">
            <Thread onSendMessage={(message) => {
              console.log('hello')
            setUserPrompt(message);
            handleRunAgent();
          }} />
            </div>
          </div>

          {/* RIGHT SIDE: Chat interface + VNC Viewer */}
          <div className="col-span-2 space-y-4">

            {/* VNC Viewer Section */}
            {vncShown ? (
              <div>
                <h2 className="text-xl font-bold mb-2">VNC Viewer</h2>
                <iframe
                  id="vncFrame"
                  title="vncFrame"
                  src="http://localhost:6080/vnc.html?host=localhost&port=5900&password=secret&autoconnect=true"
                  width="1280"
                  height="720"
                  frameBorder="0"
                />
              </div>
            ) : (
              <div className="text-blue-600">
                <h2 className="text-xl font-bold">VNC Viewer</h2>
                <p>VNC Viewer not opened yet. Click "Open VNC Viewer" on the left.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </AssistantRuntimeProvider>
  );
}
