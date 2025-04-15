"use client";

import React, { useState } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import { Play, LoaderCircle, Lightbulb, LaptopMinimal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MyRuntimeProvider } from "@/components/assistant-ui/MyRuntimeProvider";
import { SessionProvider } from "@/components/assistant-ui/SessionContext";
import Logo from "@/components/images/spongecake-logo-light.png";
import { API_BASE_URL, getVncUrl } from "@/config";

export default function Home() {
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [containerLoading, setContainerLoading] = useState(false);
  const [novncPort, setNovncPort] = useState<number>(6080); // Default port, will be updated
  const [host, setHost] = useState("");

  const handleStartContainer = async (host: string = "") => {
    try {
      if(host != 'local') {
        setContainerLoading(true);
      }
      const resp = await fetch(`${API_BASE_URL}/api/start-container`, {
        method: "POST",
        body: JSON.stringify({ host }),
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await resp.json();
      console.log("Container logs:", data.logs);
      console.log("NoVNC port:", data.novncPort);
      
      // Update the noVNC port from the server response
      if (data.novncPort) {
        setNovncPort(data.novncPort);
      }

      if(host != 'local') {
        await new Promise(resolve => setTimeout(resolve, 3500));
        setContainerStarted(true);
        setVncShown(true);
      } 
      // Wait for 2 seconds before showing the VNC viewer
      setLogs(data.logs || []);

      setHost(host);
      setContainerLoading(false);
    } catch (error) {
      console.error("Error starting container:", error);
    }
  };

  return (
    <SessionProvider>
      <MyRuntimeProvider>
        <main className="px-4 py-4 flex-col gap-3 flex items-center">
        <img src={Logo.src} alt="Spongecake Logo" width={300} />
        {!containerStarted && host == '' && (
          <div className="flex flex-row gap-2">
          <Button
            disabled={containerLoading}
            className="w-fit font-bold"
            onClick={() => handleStartContainer('')}
          >
            {containerLoading ? <LoaderCircle className="animate-spin" /> : <Play className="" />} Start Docker Agent
          </Button>
          <Button
            // disabled={desktopLoading}
            className="w-fit font-bold"
            variant={'outline'}
            onClick={() => handleStartContainer('local')}
          >
            <LaptopMinimal />    
            <span className="flex flex-row gap-1 items-center">  
            Run locally <p className="text-xs text-gray-400">MacOS only</p>
            </span>
          </Button>
          </div>
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
            )}  */}
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
        {/* Local mode - this will just show a chat window which will execute agent on local machine with no container */}
        {host === 'local' && (
          <div className="flex flex-col gap-3">
            <div className="flex text-yellow-900 flex-row gap-1 bg-yellow-100 w-fit self-center p-3 rounded-lg">
              <Lightbulb className="w-5 mr-1"/> 
              <strong>Note: </strong>Ensure this window is always visible as the agent runs
            </div>
                <div 
                style={{ height: "calc(100vh - 200px)" }} // subtract 100px or whatever value
                className=" flex flex-col border items-center mt-0 w-dvh rounded p-2">
                  <Thread />
                </div>
            </div>
          )}


        </main>
      </MyRuntimeProvider>
    </SessionProvider>
  );
}
