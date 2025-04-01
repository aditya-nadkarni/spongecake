"use client";

import React, { useState } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import { Play, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MyRuntimeProvider } from "@/components/assistant-ui/MyRuntimeProvider";
import Logo from "@/components/images/spongecake-logo-light.png";
import { API_BASE_URL, getVncUrl } from "@/config";

export default function Home() {
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [desktopLoading, setDesktopLoading] = useState(false);
  const [novncPort, setNovncPort] = useState<number>(6080); // Default port, will be updated

  const handleStartContainer = async () => {
    try {
      setDesktopLoading(true);
      const resp = await fetch(`${API_BASE_URL}/api/start-container`, {
        method: "POST",
      });
      const data = await resp.json();
      console.log("Container logs:", data.logs);
      console.log("NoVNC port:", data.novncPort);
      
      // Update the noVNC port from the server response
      if (data.novncPort) {
        setNovncPort(data.novncPort);
      }

      // Wait for 2 seconds before showing the VNC viewer
      await new Promise(resolve => setTimeout(resolve, 2000));
      setLogs(data.logs || []);
      setContainerStarted(true);
      setVncShown(true);
      setDesktopLoading(false);
    } catch (error) {
      console.error("Error starting container:", error);
    }
  };

  return (
    <MyRuntimeProvider>
      <main className="px-4 py-4 flex-col gap-3 flex items-center">
        <img src={Logo.src} alt="Spongecake Logo" width={300} />
        {!containerStarted && (
          <Button
            disabled={desktopLoading}
            className="w-fit font-bold"
            onClick={handleStartContainer}
          >
            {desktopLoading ? <LoaderCircle className="animate-spin" /> : <Play className="" />} Start Desktop
          </Button>
        )}
        {/* View Logs */}
        {/* {logs.length > 0 && (
              <div>
                <h3 className="font-bold">Logs:</h3>
                <div className="text-sm">
                  {logs.map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>
              </div>
            )} */}
        {containerStarted && vncShown && (

          <div className="grid grid-cols-3 gap-4 border w-full rounded p-2">
            <div className="col-span-1 space-y-4 overflow-auto">
              {/* LEFT COLUMN: Chat Interface */}
              <div className="border-r rounded p-2 h-[720px]">
                <Thread />
              </div>
            </div>
            {/* RIGHT COLUMN: Chat interface + VNC Viewer */}
            <div className="col-span-2 space-y-4">
              <div className="w-[100%]">
                <iframe
                  id="vncFrame"
                  title="vncFrame"
                  src={getVncUrl(novncPort)}
                  width="100%"
                  height="720"
                  frameBorder="0"
                />
                </div>
            </div>
          </div>
        )}
      </main>
    </MyRuntimeProvider>
  );
}
