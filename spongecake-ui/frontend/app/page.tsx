"use client";

import React, { useState } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import { Play, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MyRuntimeProvider } from "@/app/MyRuntimeProvider";
import Logo from "@/components/images/spongecake-logo-light.png";

export default function Home() {
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [desktopLoading, setDesktopLoading] = useState(false);

  const handleStartContainer = async () => {
    try {
      setDesktopLoading(true);
      const resp = await fetch("http://localhost:5000/api/start-container", {
        method: "POST",
      });
      const data = await resp.json();
      console.log("Container logs:", data.logs);
      setLogs(data.logs || []);
      setContainerStarted(true);
      setDesktopLoading(false);

      // Open VNC viewer
      setVncShown(true);

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
              {/* Chat Interface */}
              <div className="border-r rounded p-2 h-[720px]">
                <Thread />
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
        )}
      </main>
    </MyRuntimeProvider>
  );
}
