"use client";

import React, { useState } from "react";
import type { FC } from "react";
import {
  ActionBarPrimitive,
  BranchPickerPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
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

// ---------- Thread and its Subcomponents (consolidated from thread.tsx) ----------

export const Thread: FC<{ onSendMessage: (message: string) => void }> = ({ onSendMessage }) => {
  return (
    <ThreadPrimitive.Root
      className="bg-background box-border h-full flex flex-col overflow-hidden"
      style={{ ["--thread-max-width" as string]: "42rem" }}
    >
      <ThreadPrimitive.Viewport className="flex h-full flex-col items-center overflow-y-scroll scroll-smooth bg-inherit px-4 pt-8">
        <ThreadWelcome />
        <ThreadPrimitive.Messages
          components={{
            UserMessage: UserMessage,
            EditComposer: EditComposer,
            AssistantMessage: AssistantMessage,
          }}
        />
        <ThreadPrimitive.If empty={false}>
          <div className="min-h-8 flex-grow" />
        </ThreadPrimitive.If>
        <div className="sticky bottom-0 mt-3 flex w-full max-w-[var(--thread-max-width)] flex-col items-center justify-end rounded-t-lg bg-inherit pb-4">
          <ThreadScrollToBottom />
          <Composer onSendMessage={onSendMessage} />
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="absolute -top-8 rounded-full disabled:invisible"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC = () => {
  return (
    <ThreadPrimitive.Empty>
      <div className="flex w-full max-w-[var(--thread-max-width)] flex-grow flex-col">
        <div className="flex w-full flex-grow flex-col items-center justify-center">
          <p className="mt-4 font-medium">How can I help you today?</p>
        </div>
        <ThreadWelcomeSuggestions />
      </div>
    </ThreadPrimitive.Empty>
  );
};

const ThreadWelcomeSuggestions: FC = () => {
  return (
    <div className="mt-3 flex w-full items-stretch justify-center gap-4">
      <ThreadPrimitive.Suggestion
        className="hover:bg-muted/80 flex max-w-sm grow basis-0 flex-col items-center justify-center rounded-lg border p-3 transition-colors ease-in"
        prompt="Book me a reservation on OpenTable"
        method="replace"
        autoSend
      >
        <span className="line-clamp-2 text-ellipsis text-sm font-semibold">
        Book me a reservation on OpenTable
        </span>
      </ThreadPrimitive.Suggestion>
      <ThreadPrimitive.Suggestion
        className="hover:bg-muted/80 flex max-w-sm grow basis-0 flex-col items-center justify-center rounded-lg border p-3 transition-colors ease-in"
        prompt="Find me leads on LinkedIn"
        method="replace"
        autoSend
      >
        <span className="line-clamp-2 text-ellipsis text-sm font-semibold">
          Find me leads on LinkedIn
        </span>
      </ThreadPrimitive.Suggestion>
    </div>
  );
};

const Composer: FC<{ onSendMessage: (message: string) => void }> = ({ onSendMessage }) => {
  const [inputText, setInputText] = useState("");

  const handleSubmit = () => {
    console.log("hello world2");
    if (inputText.trim() === "") return;
    onSendMessage(inputText);
    setInputText(""); // clear the input after sending
  };

  return (
    <ComposerPrimitive.Root className="focus-within:border-ring/20 flex w-full flex-wrap items-end rounded-lg border bg-inherit px-2.5 shadow-sm transition-colors ease-in">
      <ComposerPrimitive.Input
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        rows={1}
        autoFocus
        placeholder="Write a message..."
        className="placeholder:text-muted-foreground max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm outline-none focus:ring-0 disabled:cursor-not-allowed"
      />
      <ComposerAction onSend={handleSubmit} />
    </ComposerPrimitive.Root>
  );
};

const ComposerAction: FC<{ onSend: () => void }> = ({ onSend }) => {
  return (
    <ThreadPrimitive.If running={false}>
      <ComposerPrimitive.Send asChild>
        <TooltipIconButton
          tooltip="Send"
          variant="default"
          className="my-2.5 size-8 p-2 transition-opacity ease-in"
          onClick={onSend}
        >
          <SendHorizontalIcon />
        </TooltipIconButton>
      </ComposerPrimitive.Send>
    </ThreadPrimitive.If>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="grid auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] gap-y-2 [&:where(>*)]:col-start-2 w-full max-w-[var(--thread-max-width)] py-4">
      <UserActionBar />
      <div className="bg-muted text-foreground max-w-[calc(var(--thread-max-width)*0.8)] break-words rounded-3xl px-5 py-2.5 col-start-2 row-start-2">
        <MessagePrimitive.Content />
      </div>
      <BranchPicker className="col-span-full col-start-1 row-start-3 -mr-1 justify-end" />
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="flex flex-col items-end col-start-1 row-start-2 mr-3 mt-2.5"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const EditComposer: FC = () => {
  return (
    <ComposerPrimitive.Root className="bg-muted my-4 flex w-full max-w-[var(--thread-max-width)] flex-col gap-2 rounded-xl">
      <ComposerPrimitive.Input className="text-foreground flex h-8 w-full resize-none bg-transparent p-4 pb-0 outline-none" />
      <div className="mx-3 mb-3 flex items-center justify-center gap-2 self-end">
        <ComposerPrimitive.Cancel asChild>
          <Button variant="ghost">Cancel</Button>
        </ComposerPrimitive.Cancel>
        <ComposerPrimitive.Send asChild>
          <Button>Send</Button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
};

const AssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="grid grid-cols-[auto_auto_1fr] grid-rows-[auto_1fr] relative w-full max-w-[var(--thread-max-width)] py-4">
      <div className="text-foreground max-w-[calc(var(--thread-max-width)*0.8)] break-words leading-7 col-span-2 col-start-2 row-start-1 my-1.5">
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
      </div>
      <AssistantActionBar />
      <BranchPicker className="col-start-2 row-start-2 -ml-2 mr-2" />
    </MessagePrimitive.Root>
  );
};

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="text-muted-foreground flex gap-1 col-start-3 row-start-2 -ml-1 data-[floating]:bg-background data-[floating]:absolute data-[floating]:rounded-md data-[floating]:border data-[floating]:p-1 data-[floating]:shadow-sm"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
    </ActionBarPrimitive.Root>
  );
};

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({ className, ...rest }) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn("text-muted-foreground inline-flex items-center text-xs", className)}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};

const CircleStopIcon = () => {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="16" height="16">
      <rect width="10" height="10" x="3" y="3" rx="2" />
    </svg>
  );
};

// ---------- Main Page Component ----------

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
