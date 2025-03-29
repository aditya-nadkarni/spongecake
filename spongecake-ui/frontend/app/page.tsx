"use client";

import React, { useState } from "react";
import type { FC } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import {
  ArrowDownIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  PencilIcon,
  RefreshCwIcon,
  SendHorizontalIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { MyRuntimeProvider } from "@/app/MyRuntimeProvider";

export default function Home() {
  const runtime = useChatRuntime({ api: "/api/chat" });
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [agentDone, setAgentDone] = useState(false);
  const [userPrompt, setUserPrompt] = useState("");
  const [autoMode, setAutoMode] = useState(true);

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

  const handleOpenVNC = () => {
    setVncShown(true);
  };

  const handleRunAgent = async () => {
    return;
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
    <MyRuntimeProvider>
      <main className="px-4 py-4 flex-col gap-3 flex">
        <h1 className="text-2xl font-bold mb-4">🍰 Spongecake</h1>
          {/* Desktop Agent Controls */}
          <div style={{ marginTop: "8px" }}>
              <input
                type="checkbox"
                checked={autoMode}
                onChange={() => setAutoMode(!autoMode)}
              />
              <label style={{ marginLeft: "4px" }}>Auto mode</label>
            </div>
            {!containerStarted ? (
              <Button
                className="w-fit"
                onClick={handleStartContainer}
              >
                Start Desktop + noVNC
              </Button>
            ) : (
              <div className="text-green-600 font-semibold">
                Container + noVNC are started!
              </div>
            )}
            {containerStarted && !vncShown && (
              <Button
                className="w-fit"
                onClick={handleOpenVNC}
              >
                Open VNC Viewer
              </Button>
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
        <div className="grid grid-cols-3 gap-4 border w-full rounded p-2">
          <div className="col-span-1 space-y-4 overflow-auto">
            {/* Chat Interface */}
            <div className="border-r rounded p-2 h-[720px]">
              <Thread
                onSendMessage={(message) => {
                  setUserPrompt(message);
                  handleRunAgent();
                }}
              />
            </div>
          </div>
          {/* RIGHT SIDE: Chat interface + VNC Viewer */}
          <div className="col-span-2 space-y-4">
            {vncShown ? (
              <div className="w-[100%]">
                <iframe
                  id="vncFrame"
                  title="vncFrame"
                  src="http://localhost:6080/vnc.html?host=localhost&port=5900&password=secret&autoconnect=true"
                  width="100%"
                  height="720"
                  frameBorder="0"
                />
              </div>
            ) : (
              <div className="text-blue-600">
                <h2 className="text-xl font-bold">VNC Viewer</h2>
                <p>
                  VNC Viewer not opened yet. Click "Open VNC Viewer" on the left.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </MyRuntimeProvider>
  );
}
