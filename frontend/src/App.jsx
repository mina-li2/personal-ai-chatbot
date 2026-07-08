import { useState, useRef, useEffect } from "react";

// Change this if your backend runs somewhere other than localhost:8000
const API_URL = "http://localhost:8000/chat";

function Message({ role, text }) {
  return (
    <div className={`msg ${role}`}>
      <div className="bubble">{text}</div>
    </div>
  );
}

//Use your name here if you want to personalize the assistant's greeting message.

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! I'm an assistant that knows about Minali's projects and background. Ask me anything.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });

      if (res.status === 429) {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: "You're sending messages a bit fast — please wait a moment and try again.",
          },
        ]);
        return;
      }

      if (!res.ok) throw new Error(`Server returned ${res.status}`);

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", text: data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: `Something went wrong reaching the assistant. Is the backend running? (${err.message})`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  //Use your name here.
  return (
    <div className="app">
      <header>
        <div className="eyebrow">Minali's Virtual Assistant</div>
        <h1>Ask about Minali</h1>
      </header>

      <div id="messages">
        {messages.map((m, i) => (
          <Message key={i} role={m.role} text={m.text} />
        ))}
        {loading && <div className="typing">thinking...</div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about her projects, skills, work..."
          autoComplete="off"
        />
        <button type="submit" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}