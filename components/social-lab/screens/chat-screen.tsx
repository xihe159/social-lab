import { RefreshCw, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatMessage, Persona } from "@/lib/social-lab-types";

type ChatScreenProps = {
  title: string;
  persona: Persona;
  messages: ChatMessage[];
  onSend: (message: string) => void;
  onReset: () => void;
  onFinish: () => void;
  initialDraft: string;
  isSending: boolean;
  isFinishing: boolean;
  conversationEnded: boolean;
};

export function ChatScreen({
  title,
  persona,
  messages,
  onSend,
  onReset,
  onFinish,
  initialDraft,
  isSending,
  isFinishing,
  conversationEnded,
}: ChatScreenProps) {
  const [draft, setDraft] = useState(initialDraft);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDraft(initialDraft);
  }, [initialDraft]);

  useEffect(() => {
    chatWindowRef.current?.scrollTo({
      top: chatWindowRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isSending]);

  const send = () => {
    const value = draft.trim();
    if (!value || isSending || conversationEnded) return;
    onSend(value);
    setDraft("");
  };

  return (
    <section className="screen chat-screen is-current">
      <div className="chat-top">
        <div>
          <h2>{title}</h2>
          <p>当前态度：谨慎</p>
        </div>
        <button
          className="secondary-action compact-button"
          disabled={isSending || isFinishing}
          onClick={onReset}
          type="button"
        >
          <RefreshCw size={16} /> 重新开始
        </button>
      </div>

      <div className="state-chip">对方目前关注：{persona.focus}</div>

      <div className="chat-window" ref={chatWindowRef} aria-live="polite">
        {isSending && (
          <p className="typing-status" role="status">
            对方正在输入中...
          </p>
        )}
        {messages.map((message) =>
          message.role === "system" ? (
            <p className="chat-status" key={message.id}>
              {message.text}
            </p>
          ) : (
            <p className={`bubble ${message.role}`} key={message.id}>
              {message.text}
            </p>
          ),
        )}
      </div>

      <div className="composer">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") send();
          }}
          disabled={isSending || isFinishing || conversationEnded}
          placeholder={
            conversationEnded ? "对方已结束本次交流" : "输入下一句话..."
          }
        />
        <button
          className="send-button"
          onClick={send}
          disabled={isSending || isFinishing || conversationEnded}
          aria-label="发送"
          title="发送"
          type="button"
        >
          <Send size={20} />
        </button>
      </div>
      <button
        className="dark-action"
        disabled={isSending || isFinishing}
        onClick={onFinish}
        type="button"
      >
        {isFinishing ? "正在生成分析..." : "结束模拟并查看分析"}
      </button>
    </section>
  );
}
