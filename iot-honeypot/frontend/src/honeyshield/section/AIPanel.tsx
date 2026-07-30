import { AnimatePresence, motion } from 'framer-motion';
import { Bot, BrainCircuit, ChevronRight, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { aiInsights, severityColor, type Severity } from '../lib/mock-data';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { SectionHeader } from '../components/fx/SectionHeader';

const promptChips = [
  'Show top attackers',
  'Recommend firewall rules',
  'Summarize Mirai activity',
  'Predict next-hour risk',
];

function toneFor(text: string): Severity {
  if (/block|recommend|critical/i.test(text)) return 'critical';
  if (/increase|spike|anomaly/i.test(text)) return 'high';
  if (/detect|observe|attempt/i.test(text)) return 'medium';
  return 'low';
}

type Msg = { role: 'ai' | 'user'; text: string; tone?: Severity };

export function AIPanel() {
  const [messages, setMessages] = useState<Msg[]>(
    aiInsights.slice(0, 4).map((t) => ({ role: 'ai', text: t, tone: toneFor(t) }))
  );
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, thinking]);

  useEffect(() => {
    const id = setInterval(() => {
      const aiCount = messages.filter((m) => m.role === 'ai').length;
      const tip = aiInsights[aiCount % aiInsights.length];
      setMessages((prev) => [...prev, { role: 'ai' as const, text: tip, tone: toneFor(tip) }].slice(-12));
    }, 9000);
    return () => clearInterval(id);
  }, [messages]);

  function clearChat() {
    setMessages([]);
  }

  function send(text: string) {
    if (!text.trim()) return;
    setMessages((p) => [...p, { role: 'user', text }]);
    setInput('');
    setThinking(true);
    setTimeout(() => {
      const aiCount = messages.filter((m) => m.role === 'ai').length + 1;
      const reply = aiInsights[(aiCount + 2) % aiInsights.length];
      setMessages((p) => [...p, { role: 'ai', text: reply, tone: toneFor(reply) }]);
      setThinking(false);
    }, 1100);
  }

  return (
    <section className="container py-12 md:py-16">
      <SectionHeader
        eyebrow="AI Engine"
        title="AI Threat Analyst"
        subtitle="HoneyShield AI continuously reasons over the attack stream and recommends countermeasures."
        right={
          <Badge variant="success">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#00FF88]" /> Online
          </Badge>
        }
      />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card className="flex h-[560px] flex-col p-0">
          <CardHeader className="border-b border-[#1F2A44]">
            <div className="flex items-center justify-between">
              <CardTitle>
                <span className="flex items-center gap-2">
                  <BrainCircuit className="h-4 w-4 text-[#00BFFF]" /> HoneyShield AI Console
                </span>
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="default">
                  <Sparkles className="h-3 w-3" /> GPT-class
                </Badge>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={clearChat}
                  disabled={messages.length === 0}
                  aria-label="Clear chat"
                  className="text-[#8A9BB8] hover:text-[#FF3D6E]"
                >
                  <Trash2 className="mr-1 h-3.5 w-3.5" />
                  Clear chat
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <div ref={scrollRef} className="h-[360px] overflow-y-auto p-5">
              <AnimatePresence initial={false}>
                {messages.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid h-full place-items-center text-center"
                  >
                    <div>
                      <BrainCircuit className="mx-auto h-8 w-8 text-[#00BFFF]/60" />
                      <p className="mt-2 text-sm text-[#E6F1FF]">Chat cleared.</p>
                      <p className="mt-1 text-xs text-[#8A9BB8]">
                        Tap a prompt chip below or ask your own question.
                      </p>
                    </div>
                  </motion.div>
                )}
                {messages.map((m, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`mb-3 flex ${m.role === 'ai' ? 'justify-start' : 'justify-end'}`}
                  >
                    {m.role === 'ai' ? (
                      <div className="max-w-[85%]">
                        <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wider text-[#8A9BB8]">
                          <Bot className="h-3 w-3 text-[#00BFFF]" /> HoneyShield AI
                        </div>
                        <div
                          className="rounded-lg border bg-[#00BFFF]/5 px-4 py-2.5 text-sm text-[#E6F1FF] shadow-[inset_0_0_18px_rgba(0,191,255,0.06)]"
                          style={{
                            borderColor: m.tone ? severityColor(m.tone) + '60' : '#00BFFF60',
                            background: m.tone ? severityColor(m.tone) + '08' : undefined,
                          }}
                        >
                          {m.text}
                        </div>
                      </div>
                    ) : (
                      <div className="max-w-[80%] rounded-lg border border-[#1F2A44] bg-[#0F1626]/80 px-4 py-2.5 text-sm text-[#E6F1FF]">
                        {m.text}
                      </div>
                    )}
                  </motion.div>
                ))}
                {thinking && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mb-3 flex items-center gap-2 text-xs text-[#8A9BB8]"
                  >
                    <Bot className="h-3 w-3 text-[#00BFFF]" /> HoneyShield AI is analyzing…
                    <span className="ml-2 flex gap-1">
                      {[0, 1, 2].map((d) => (
                        <motion.span
                          key={d}
                          className="h-1.5 w-1.5 rounded-full bg-[#00BFFF]"
                          animate={{ opacity: [0.2, 1, 0.2] }}
                          transition={{ duration: 1, repeat: Infinity, delay: d * 0.15 }}
                        />
                      ))}
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <div className="border-t border-[#1F2A44] p-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  send(input);
                }}
                className="flex items-center gap-2"
              >
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask HoneyShield AI about the current threat landscape…"
                />
                <Button type="submit" size="icon" aria-label="Send">
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </form>
              <div className="mt-3 flex flex-wrap gap-2">
                {promptChips.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    className="rounded-full border border-[#1F2A44] bg-[#0F1626]/70 px-3 py-1 text-[10px] uppercase tracking-wider text-[#8A9BB8] hover:border-[#00BFFF]/50 hover:text-[#00BFFF]"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
              <Sparkles className="h-3.5 w-3.5 text-[#FFD600]" /> Latest Recommendations
            </h3>
            <ul className="space-y-3">
              {[
                'Block ASN 12345 — Mirai infrastructure',
                'Patch CVE-2024-12345 on camera honeypot',
                'Rate-limit SSH on edge proxy to 30/min',
                'Quarantine hp-telnet-02 for forensic capture',
              ].map((r, i) => (
                <motion.li
                  key={r}
                  initial={{ opacity: 0, x: 12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className="flex items-start gap-3 rounded-lg border border-[#1F2A44] bg-[#0F1626]/70 p-3 text-sm"
                >
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#00FF88]" />
                  <span className="text-[#E6F1FF]">{r}</span>
                </motion.li>
              ))}
            </ul>
          </Card>
          <Card className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
              <BrainCircuit className="h-3.5 w-3.5 text-[#00E5FF]" /> Anomaly Forecast
            </h3>
            <p className="text-sm text-[#E6F1FF]">
              Expected next-hour <span className="neon-text">attack volume</span> for{' '}
              <span className="text-[#FFD600]">SSH</span>:{' '}
              <span className="font-mono text-[#00BFFF]">+18%</span>
            </p>
            <p className="mt-2 text-xs text-[#8A9BB8]">
              Confidence: <span className="text-[#00FF88]">92%</span> · Model:{' '}
              <span className="text-[#E6F1FF]">honeyshield-v3</span>
            </p>
          </Card>
        </div>
      </div>
    </section>
  );
}