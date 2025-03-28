import React, { useState } from "react";

function App() {
  const [containerStarted, setContainerStarted] = useState(false);
  const [vncShown, setVncShown] = useState(false);
  const [agentDone, setAgentDone] = useState(false);

  // Text input + autoMode
  const [userPrompt, setUserPrompt] = useState("");
  const [autoMode, setAutoMode] = useState(true);

  // Logs from the server
  const [logs, setLogs] = useState([]);

  // 1) Start the container + noVNC
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

  // 2) Toggle the VNC viewer iframe
  const handleOpenVNC = () => {
    setVncShown(true);
  };

  // 3) Run the agent with user prompt
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
    <div style={{ padding: "20px" }}>
      <h1>Desktop Agent UI (Flask Backend)</h1>

      <div style={{ display: "flex", gap: "40px" }}>
        {/* LEFT COLUMN */}
        <div style={{ flex: "1", maxWidth: "300px" }}>
          {/* Prompt Input */}
          <div>
            <label>Enter your prompt:</label>
            <input
              style={{ width: "100%", marginTop: "4px" }}
              type="text"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
            />
          </div>

          {/* Auto-mode Checkbox */}
          <div style={{ marginTop: "8px" }}>
            <input
              type="checkbox"
              checked={autoMode}
              onChange={() => setAutoMode(!autoMode)}
            />
            <label style={{ marginLeft: "4px" }}>Auto mode</label>
          </div>

          {/* 1) Start Container Button */}
          {!containerStarted ? (
            <button style={{ marginTop: "16px" }} onClick={handleStartContainer}>
              Start Desktop + noVNC
            </button>
          ) : (
            <div style={{ marginTop: "16px", color: "green" }}>
              Container + noVNC are started!
            </div>
          )}

          {/* 2) Show VNC Viewer */}
          {containerStarted && !vncShown && (
            <button style={{ marginTop: "16px" }} onClick={handleOpenVNC}>
              Open VNC Viewer
            </button>
          )}

          {/* 3) Run the Agent */}
          {vncShown && !agentDone && (
            <button style={{ marginTop: "16px" }} onClick={handleRunAgent}>
              Run Agent Action
            </button>
          )}

          {agentDone && (
            <div style={{ marginTop: "16px", color: "green" }}>
              The agent has finished its task!
            </div>
          )}

          {/* Logs */}
          {logs.length > 0 && (
            <div style={{ marginTop: "16px" }}>
              <h3>Logs:</h3>
              {logs.map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ flex: "2" }}>
          {vncShown ? (
            <div>
              <h2>VNC Viewer</h2>
              <iframe
  id="vncFrame"
  title="vncFrame"
  src="http://localhost:6080/vnc.html?host=localhost&port=5900&password=secret&autoconnect=true"
  width="1024"
  height="768"
  frameBorder="0"
  onLoad={() => {
    // Attempt to inject CSS if same-origin
    const iframeDoc = document.getElementById("vncFrame").contentDocument;
    if (iframeDoc) {
      const style = iframeDoc.createElement("style");
      style.innerHTML = `
      #noVNC_control_bar,
      #noVNC_control_bar_anchor,
      #noVNC_logo {
        display: none !important;
        visibility: hidden !important;
      }
    `;

      iframeDoc.head.appendChild(style);
    }
  }}
/>

            </div>
          ) : (
            <div>
              <h2>VNC Viewer</h2>
              <p style={{ color: "blue" }}>
                VNC Viewer not opened yet. Click &quot;Open VNC Viewer&quot; on the
                left.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
