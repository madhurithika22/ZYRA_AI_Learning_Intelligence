"use client";

import React, { useState } from "react";
import { sendChatMessage } from "../lib/api";
import { AuthUser, ChatMessage, LearnerAppStateResponse } from "../lib/types";
import { Button } from "./ui/Button";

interface AssistantViewProps {
  user: AuthUser;
  appState?: LearnerAppStateResponse | null;
  onNavigateTab?: (tab: string) => void;
}

export function AssistantView({ user, appState, onNavigateTab }: AssistantViewProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const suggestedQuestions = [
    "Why is Model Deployment my bottleneck?",
    "Why is Docker my next action?",
    "What evidence supports my skill confidence?",
    "Why did my learning path change?",
  ];

  const [msgCounter, setMsgCounter] = useState(1);

  async function handleSend(textToSend?: string) {
    const msgText = textToSend || input;
    if (!msgText.trim() || sending) return;

    const currentId = msgCounter;
    setMsgCounter((c) => c + 2);

    const userMsg: ChatMessage = {
      id: `usr-${currentId}`,
      sender: "user",
      content: msgText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setSending(true);

    try {
      const res = await sendChatMessage(user.learner_id, sessionId, msgText);
      setSessionId(res.session_id);

      const assistantMsg: ChatMessage = {
        id: res.message_id || `ast-${currentId + 1}`,
        sender: "assistant",
        content: typeof res.content === "string" ? res.content : JSON.stringify(res.content),
        sources: res.sources,
        suggestedFollowups: res.suggested_followups,
        responseType: res.response_type,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const msgTextErr = err instanceof Error ? err.message : "I could not retrieve an authoritative answer at this moment.";
      const errorMsg: ChatMessage = {
        id: `err-${currentId + 1}`,
        sender: "assistant",
        content: msgTextErr,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-6">
      {onNavigateTab && (
        <button
          type="button"
          onClick={() => onNavigateTab("overview")}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
        >
          <span>←</span>
          <span>Back to Overview</span>
        </button>
      )}

      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs flex flex-col h-[650px] space-y-6">
        {/* Header */}
        <div className="border-b border-subtle pb-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
              Grounded AI System
            </span>
            <h2 className="text-2xl font-extrabold text-primary">Learning Assistant</h2>
            <p className="text-xs text-secondary mt-0.5">
              Ask why your system made a decision or query your demonstrated evidence.
            </p>
          </div>
        </div>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-6">
          {appState && (appState.stage === "GOAL_REQUIRED" || appState.stage === "DIAGNOSTIC_REQUIRED") && (
            <div className="bg-subtle/50 border border-subtle p-6 rounded-2xl text-center space-y-4 my-4">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                YOUR LEARNING ASSISTANT
              </span>
              <p className="text-xs text-secondary max-w-md mx-auto leading-relaxed">
                Complete your goal definition and diagnostic check first. Then your assistant can explain your bottlenecks, next action, learning path, and evidence.
              </p>
              {onNavigateTab && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onNavigateTab(appState.next_action_route)}
                >
                  Continue Setup →
                </Button>
              )}
            </div>
          )}

          {messages.length === 0 ? (
            <div className="py-8 text-center space-y-6">
              <p className="text-sm text-secondary">
                Select a suggested question or type your prompt below:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(q)}
                    className="p-4 rounded-2xl bg-subtle/40 border border-subtle hover:border-hover text-left text-xs font-medium text-primary transition-all"
                  >
                    &quot;{q}&quot;
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-2xl p-5 rounded-3xl text-sm leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-accent-primary text-white font-medium shadow-xs"
                      : "bg-subtle/50 text-primary border border-subtle"
                  }`}
                >
                  {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}

                  {/* Sources & Citations Drawer */}
                  {((msg.sources && msg.sources.length > 0) || (msg.citations && msg.citations.length > 0)) && (
                    <div className="mt-4 pt-3 border-t border-subtle/40 space-y-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-secondary block">
                        Authoritative Sources:
                      </span>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {msg.sources?.map((s, idx) => (
                          <span
                            key={`src-${idx}`}
                            className="px-2.5 py-1 rounded-lg bg-surface text-secondary text-[11px] border border-subtle font-medium"
                          >
                            📌 {s.label || `${s.source_type}: ${s.source_id}`}
                          </span>
                        ))}
                        {msg.citations?.map((c, idx) => (
                          <span
                            key={`cit-${idx}`}
                            className="px-2.5 py-1 rounded-lg bg-surface text-secondary text-[11px] border border-subtle font-medium"
                          >
                            {typeof c === "string" ? c : JSON.stringify(c)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input Bar */}
        <div className="pt-4 border-t border-subtle flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask why your system made a decision..."
            className="flex-1 bg-subtle/50 border border-subtle rounded-2xl px-5 py-3.5 text-sm text-primary placeholder-muted focus:outline-none focus:border-accent-primary transition-all"
          />
          <Button
            variant="primary"
            size="md"
            onClick={() => handleSend()}
            disabled={sending || !input.trim()}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
