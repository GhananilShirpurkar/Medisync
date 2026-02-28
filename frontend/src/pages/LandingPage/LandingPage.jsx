import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import {
  Mic, Camera, BellRing, Shield, Package, Truck, Brain,
  Eye, ChevronDown, ChevronRight, Play, Check, ArrowRight,
  Mail, Phone, MapPin, Zap, Clock, Activity, Star,
  MessageSquare, Volume2, Languages, History
} from 'lucide-react';
import './LandingPage.css';

gsap.registerPlugin(ScrollTrigger);

const FRAME_COUNT = 163;

function drawFrame(canvas, img) {
  if (!canvas || !img || !img.complete || img.naturalWidth === 0) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  const dpr = window.devicePixelRatio || 1;
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, w, h);
  // Cover mode — fill the square canvas completely
  const imgRatio = img.naturalWidth / img.naturalHeight;
  const canvasRatio = w / h;
  let dw, dh;
  if (canvasRatio > imgRatio) { dw = w; dh = w / imgRatio; }
  else { dh = h; dw = h * imgRatio; }
  ctx.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
  ctx.restore();
}

/* ── Agent data ──────────────────────────── */
const agents = [
  { icon: Mic, name: 'FrontDesk Agent', emoji: '🎙️', desc: 'Natural voice conversations, intent classification, patient context extraction' },
  { icon: Eye, name: 'Vision Agent', emoji: '👁️', desc: 'OCR prescription scanning, document validation, compliance checking' },
  { icon: Shield, name: 'MedicalValidation', emoji: '⚕️', desc: 'Drug interaction checks, age verification, contraindication alerts' },
  { icon: Package, name: 'Inventory Agent', emoji: '📦', desc: 'Real-time stock (77 medicines), generic alternatives, prescription enforcement' },
  { icon: Truck, name: 'Fulfillment Agent', emoji: '🚚', desc: 'Order processing, webhook integration, real-world action triggers' },
  { icon: Brain, name: 'ProactiveIntel', emoji: '🔮', desc: 'Refill prediction, consumption analysis, async monitoring' },
];

const stats = [
  { value: '6', label: 'AI Agents Active' },
  { value: '146', label: 'Symptom Mappings' },
  { value: '88%', label: 'Accuracy Rate' },
  { value: '24/7', label: 'Always On' },
];

const steps = [
  { icon: Mic, title: 'Voice Input', desc: 'Patient describes symptoms naturally', num: '01' },
  { icon: Brain, title: 'AI Processing', desc: 'Agents analyze and validate in real-time', num: '02' },
  { icon: Shield, title: 'Safe Recommendation', desc: 'Validated medicine with safety checks', num: '03' },
];

const testimonials = [
  { quote: 'MediSync reduced our prescription processing time by 60%', author: 'Apollo Pharmacy Manager', stars: 5 },
  { quote: 'The voice interface helps our elderly patients immensely', author: 'Local Chemist Owner', stars: 5 },
  { quote: 'Finally, AI that doesn\'t hallucinate medical advice', author: 'Hospital Administrator', stars: 5 },
];

const safetyFeatures = [
  'Drug interaction detection',
  'Age-appropriate dosing',
  'Contraindication alerts',
  'Prescription requirement enforcement',
  'Complete audit trails',
];

const faqs = [
  { q: 'How does the multi-agent system work?', a: 'Six specialized AI agents collaborate in a pipeline — from voice intake through medical validation to inventory lookup — each contributing domain expertise to deliver safe, accurate recommendations.' },
  { q: 'Is patient data secure and HIPAA compliant?', a: 'Yes. All data is encrypted at rest and in transit. We follow HIPAA guidelines with complete audit trails and no persistent storage of personal health information beyond the session.' },
  { q: 'Can it integrate with existing pharmacy software?', a: 'MediSync exposes a REST API and webhook system that integrates with major pharmacy management systems, POS platforms, and inventory databases.' },
  { q: 'What languages does the voice interface support?', a: 'Currently English and Hindi with Whisper-powered transcription. Additional languages are being added based on demand.' },
];

const techStack = ['LangGraph', 'Langfuse', 'OpenAI Whisper', 'SQLite', 'Supabase', 'FastAPI', 'React'];

/* ── Component ──────────────────────────── */
const LandingPage = () => {
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const imagesRef = useRef([]);
  const [openFaq, setOpenFaq] = useState(null);

  // Enable scrolling (global.css locks it for other pages)
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const oHO = html.style.overflow, oHH = html.style.height;
    const oBO = body.style.overflow, oBH = body.style.height;
    html.style.overflow = 'auto'; html.style.height = 'auto';
    body.style.overflow = 'auto'; body.style.height = 'auto';
    body.style.background = 'linear-gradient(135deg, #eef4ff 0%, #f0f7ff 50%, #f7f9fc 100%)';
    return () => { html.style.overflow = oHO; html.style.height = oHH; body.style.overflow = oBO; body.style.height = oBH; body.style.background = ''; };
  }, []);

  // Preload frames
  useEffect(() => {
    let loaded = 0;
    const imgs = new Array(FRAME_COUNT);
    for (let i = 0; i < FRAME_COUNT; i++) {
      const img = new Image();
      img.src = `/ezgif-frame-${String(i + 1).padStart(3, '0')}.jpg`;
      img.onload = () => {
        loaded++;
        setProgress(Math.round((loaded / FRAME_COUNT) * 100));
        if (i === 0) drawFrame(canvasRef.current, img);
        if (loaded === FRAME_COUNT) { imagesRef.current = imgs; setReady(true); }
      };
      img.onerror = () => { loaded++; if (loaded === FRAME_COUNT) { imagesRef.current = imgs; setReady(true); } };
      imgs[i] = img;
    }
  }, []);

  // Auto-play animation loop
  useEffect(() => {
    if (!ready) return;
    const imgs = imagesRef.current;
    const canvas = canvasRef.current;
    if (!canvas || imgs.length === 0) return;
    drawFrame(canvas, imgs[0]);
    let frame = 0;
    let lastTime = 0;
    const fps = 30;
    const interval = 1000 / fps;
    let rafId;
    const animate = (time) => {
      rafId = requestAnimationFrame(animate);
      if (time - lastTime < interval) return;
      lastTime = time;
      frame = (frame + 1) % FRAME_COUNT;
      if (imgs[frame]) drawFrame(canvas, imgs[frame]);
    };
    rafId = requestAnimationFrame(animate);
    const onResize = () => { if (imgs[frame]) drawFrame(canvas, imgs[frame]); };
    window.addEventListener('resize', onResize);
    return () => { cancelAnimationFrame(rafId); window.removeEventListener('resize', onResize); };
  }, [ready]);

  // Scroll reveal animations
  useEffect(() => {
    if (!ready) return;
    gsap.utils.toArray('.reveal-up').forEach(el => {
      gsap.fromTo(el, { y: 60, opacity: 0 }, {
        y: 0, opacity: 1, duration: 0.8, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', toggleActions: 'play none none none' }
      });
    });
  }, [ready]);

  // Floating medical icons for background
  const medicalIcons = [
    { emoji: '💊', top: '15%', left: '10%', delay: '0s', size: '2rem' },
    { emoji: '🩺', top: '25%', left: '85%', delay: '1.5s', size: '2.5rem' },
    { emoji: '🧪', top: '65%', left: '5%', delay: '2s', size: '2.2rem' },
    { emoji: '💉', top: '75%', left: '90%', delay: '0.5s', size: '2.4rem' },
    { emoji: '🔬', top: '45%', left: '15%', delay: '3s', size: '1.8rem' },
    { emoji: '🧠', top: '10%', left: '75%', delay: '2.5s', size: '2.1rem' },
    { emoji: '⚕️', top: '85%', left: '20%', delay: '1s', size: '2.3rem' },
  ];

  return (
    <div className="lp">
      {/* Animated Background Mesh */}
      <div className="lp-bg-mesh">
        <div className="mesh-blob blob-1"></div>
        <div className="mesh-blob blob-2"></div>
        <div className="mesh-blob blob-3"></div>
        <div className="mesh-blob blob-4"></div>
        {medicalIcons.map((icon, i) => (
          <div
            key={i}
            className="lp-bg-icon"
            style={{
              top: icon.top,
              left: icon.left,
              animationDelay: icon.delay,
              fontSize: icon.size
            }}
          >
            {icon.emoji}
          </div>
        ))}
      </div>

      {/* Loader */}
      {!ready && (
        <div className="lp-loader">
          <span className="lp-loader__brand">MEDISYNC</span>
          <div className="lp-loader__bar"><div className="lp-loader__fill" style={{ width: `${progress}%` }} /></div>
          <span className="lp-loader__pct">{progress}%</span>
        </div>
      )}

      {/* ═══ HERO — Auto-play animation + CTA ═══ */}
      <section className="lp-hero-text">
        <div className="lp-container">
          <div className="lp-hero-video">
            <canvas ref={canvasRef} id="lp-canvas" />
          </div>
          <p className="lp-hero-text__eyebrow">Agentic AI Pharmacy Assistant</p>
          <h1 className="lp-hero-text__headline">YOUR AI PHARMACIST</h1>
          <p className="lp-hero-text__sub">Listening. Learning. Predicting.</p>
          <p className="lp-hero-text__desc">AI-driven patient intake, prescription intelligence, and predictive alerts. From walk-in to warning.</p>
          <div className="lp-hero-text__ctas">
            <button className="lp-btn lp-btn--primary" onClick={() => navigate('/chat')}>
              Start Consultation <ArrowRight size={18} />
            </button>
            <button className="lp-btn lp-btn--outline" onClick={() => navigate('/admin')}>
              👤 Admin Login
            </button>
          </div>
        </div>
      </section>

      {/* ═══ STATS BAR ═══ */}
      <section className="lp-stats reveal-up">
        <div className="lp-container lp-stats__grid">
          {stats.map((s, i) => (
            <div key={i} className="lp-stats__item">
              <span className="lp-stats__value">{s.value}</span>
              <span className="lp-stats__label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ FEATURES — 6 Agents ═══ */}
      <section className="lp-features">
        <div className="lp-container">
          <p className="lp-section-eyebrow reveal-up">Intelligent Pharmacy Automation</p>
          <h2 className="lp-section-title reveal-up">Six Minds. One Mission.</h2>
          <p className="lp-section-sub reveal-up">Specialized AI agents working in harmony to transform pharmacy operations.</p>
          <div className="lp-features__grid">
            {agents.map((a, i) => (
              <div key={i} className="lp-agent-card reveal-up">
                <div className="lp-agent-card__icon-wrap">
                  <span className="lp-agent-card__emoji">{a.emoji}</span>
                </div>
                <h3 className="lp-agent-card__name">{a.name}</h3>
                <p className="lp-agent-card__desc">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section className="lp-how">
        <div className="lp-container">
          <p className="lp-section-eyebrow reveal-up">How It Works</p>
          <h2 className="lp-section-title reveal-up">From Symptom to Solution. In Seconds.</h2>
          <div className="lp-how__steps">
            {steps.map((s, i) => (
              <React.Fragment key={i}>
                <div className="lp-step reveal-up">
                  <div className="lp-step__num">{s.num}</div>
                  <div className="lp-step__icon-wrap"><s.icon size={28} /></div>
                  <h3 className="lp-step__title">{s.title}</h3>
                  <p className="lp-step__desc">{s.desc}</p>
                </div>
                {i < 2 && <div className="lp-step__arrow reveal-up"><ChevronRight size={24} /></div>}
              </React.Fragment>
            ))}
          </div>
          <div className="lp-how__timeline reveal-up">
            <div className="lp-timeline-chip">FrontDesk</div>
            <span className="lp-timeline-arrow">→</span>
            <div className="lp-timeline-chip">MedicalValidation</div>
            <span className="lp-timeline-arrow">→</span>
            <div className="lp-timeline-chip">Inventory</div>
            <span className="lp-timeline-score">Confidence: 94%</span>
          </div>
        </div>
      </section>

      {/* ═══ VOICE INTERFACE ═══ */}
      <section className="lp-voice">
        <div className="lp-container lp-voice__grid">
          <div className="lp-voice__left reveal-up">
            <p className="lp-section-eyebrow">Voice Interface</p>
            <h2 className="lp-section-title">Talk Naturally.<br />Get Answers Instantly.</h2>
            <p className="lp-section-sub">Push-to-talk voice input with Whisper transcription. Multi-language support including Hindi.</p>
            <div className="lp-voice__features">
              {[{ icon: Mic, t: 'Push-to-Talk' }, { icon: Volume2, t: 'Browser TTS' }, { icon: Languages, t: 'Multi-language' }, { icon: History, t: 'Session Memory' }].map((f, i) => (
                <div key={i} className="lp-voice__feat-chip"><f.icon size={14} /> {f.t}</div>
              ))}
            </div>
          </div>
          <div className="lp-voice__right reveal-up">
            <div className="lp-chat-mock">
              <div className="lp-chat-mock__header">MediSync Assistant</div>
              <div className="lp-chat-mock__body">
                <div className="lp-chat-bubble lp-chat-bubble--user">I have a headache and fever</div>
                <div className="lp-chat-bubble lp-chat-bubble--ai">I understand. Let me check safe options for you...</div>
                <div className="lp-chat-timeline">
                  <Activity size={14} /> <span>Processing: FrontDesk → MedicalValidation → Inventory</span>
                </div>
                <div className="lp-chat-bubble lp-chat-bubble--ai">Based on your symptoms, I recommend <strong>Paracetamol 500mg</strong>. Safe for adults. No interactions detected.</div>
              </div>
              <div className="lp-chat-mock__input">
                <Mic size={16} /> <span>Press to speak...</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ SAFETY ═══ */}
      <section className="lp-safety">
        <div className="lp-container lp-safety__grid">
          <div className="lp-safety__left reveal-up">
            <div className="lp-safety__mock">
              <div className="lp-safety__mock-header">Prescription Validation</div>
              <div className="lp-safety__mock-row"><Check size={16} className="lp-check-green" /> Patient ID verified</div>
              <div className="lp-safety__mock-row"><Check size={16} className="lp-check-green" /> Drug interaction: None found</div>
              <div className="lp-safety__mock-row"><Check size={16} className="lp-check-green" /> Age-appropriate dosage confirmed</div>
              <div className="lp-safety__mock-row lp-safety__mock-row--warn"><Zap size={16} className="lp-warn-orange" /> Prescription required: Flagged</div>
              <div className="lp-safety__badge">✓ VALIDATED</div>
            </div>
          </div>
          <div className="lp-safety__right reveal-up">
            <p className="lp-section-eyebrow">Safety First</p>
            <h2 className="lp-section-title">Medical-Grade Safety.<br />Never Compromised.</h2>
            <div className="lp-safety__badge-pill">Never Forges Data</div>
            <ul className="lp-safety__list">
              {safetyFeatures.map((f, i) => (
                <li key={i}><Check size={18} className="lp-check-green" /> {f}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ═══ OBSERVABILITY ═══ */}
      <section className="lp-observe">
        <div className="lp-container">
          <div className="lp-observe-box">
            <p className="lp-section-eyebrow reveal-up">Full Transparency</p>
            <h2 className="lp-section-title reveal-up">See What Your AI Is Thinking.</h2>
            <p className="lp-section-sub reveal-up">Real-time agent timeline with Langfuse tracing. Full transparency in every decision.</p>
            <div className="lp-observe__cards reveal-up">
              {[
                { name: 'FrontDesk', score: '96%', time: '120ms', color: '#0066FF' },
                { name: 'MedicalValidation', score: '94%', time: '240ms', color: '#00C853' },
                { name: 'Inventory', score: '99%', time: '80ms', color: '#FF6B00' },
              ].map((a, i) => (
                <div key={i} className="lp-observe__card">
                  <div className="lp-observe__card-header">
                    <span className="lp-observe__agent-dot" style={{ background: a.color }} />
                    <span className="lp-observe__agent-name">{a.name}</span>
                    <span className="lp-observe__agent-score">{a.score}</span>
                  </div>
                  <div className="lp-observe__card-meta">
                    <Clock size={12} /> {a.time} · <Activity size={12} /> 3 tool calls
                  </div>
                  <div className="lp-observe__card-trace">
                    {"{ \"agent\": \"" + a.name + "\", \"confidence\": " + a.score.replace('%', '') / 100 + " }"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══ PROACTIVE INTELLIGENCE ═══ */}
      <section className="lp-proactive">
        <div className="lp-container lp-proactive__grid">
          <div className="lp-proactive__left reveal-up">
            <p className="lp-section-eyebrow">Proactive Intelligence</p>
            <h2 className="lp-section-title">Predict Before<br />It Hurts.</h2>
            <ul className="lp-proactive__list">
              <li><BellRing size={18} /> Refill prediction based on purchase history</li>
              <li><Activity size={18} /> Consumption pattern analysis</li>
              <li><Zap size={18} /> Async background processing</li>
              <li><Shield size={18} /> Patient adherence monitoring</li>
            </ul>
          </div>
          <div className="lp-proactive__right reveal-up">
            <div className="lp-proactive__card">
              <div className="lp-proactive__card-icon"><BellRing size={32} /></div>
              <h4>Refill Alert</h4>
              <p>Paracetamol 500mg — Refill in <strong>3 days</strong></p>
              <div className="lp-proactive__bar">
                <div className="lp-proactive__bar-fill" style={{ width: '78%' }} />
              </div>
              <span className="lp-proactive__bar-label">78% consumed</span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ TESTIMONIALS ═══ */}
      <section className="lp-testi">
        <div className="lp-container">
          <p className="lp-section-eyebrow reveal-up">Social Proof</p>
          <h2 className="lp-section-title reveal-up">Trusted by Modern Pharmacies</h2>
          <div className="lp-testi__grid">
            {testimonials.map((t, i) => (
              <div key={i} className="lp-testi__card reveal-up">
                <div className="lp-testi__stars">
                  {Array.from({ length: t.stars }).map((_, j) => <Star key={j} size={16} fill="#FFB800" color="#FFB800" />)}
                </div>
                <p className="lp-testi__quote">"{t.quote}"</p>
                <p className="lp-testi__author">— {t.author}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ FAQ ═══ */}
      <section className="lp-faq">
        <div className="lp-container lp-faq__layout">
          <div className="lp-faq__left reveal-up">
            <h2 className="lp-section-title">Questions?<br />We've Got Answers.</h2>
            <div className="lp-faq__cta-box">
              <p>Get Early Access</p>
              <div className="lp-faq__email-row">
                <input type="email" placeholder="you@company.com" className="lp-faq__input" />
                <button className="lp-btn lp-btn--primary lp-btn--sm"><Mail size={16} /></button>
              </div>
            </div>
          </div>
          <div className="lp-faq__right">
            {faqs.map((f, i) => (
              <div key={i} className={`lp-faq__item reveal-up ${openFaq === i ? 'lp-faq__item--open' : ''}`} onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                <div className="lp-faq__q">
                  <span>{f.q}</span>
                  <ChevronDown size={18} className="lp-faq__chevron" />
                </div>
                <div className="lp-faq__a"><p>{f.a}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="lp-footer">
        <div className="lp-container lp-footer__grid">
          <div className="lp-footer__brand">
            <h3>MediSync</h3>
            <p>Your AI Front Desk.<br />Listening. Learning. Predicting.</p>
          </div>
          <div className="lp-footer__col">
            <h4>Product</h4>
            <a href="#">Features</a><a href="#">Pricing</a><a href="#">API Docs</a><a href="#">Changelog</a>
          </div>
          <div className="lp-footer__col">
            <h4>Company</h4>
            <a href="#">About</a><a href="#">Blog</a><a href="#">Careers</a><a href="#">Contact</a>
          </div>
          <div className="lp-footer__col">
            <h4>Legal</h4>
            <a href="#">Privacy</a><a href="#">Terms</a><a href="#">Security</a>
          </div>
        </div>
        <div className="lp-container lp-footer__bottom">
          <span>© 2026 MediSync. Agentic AI for Healthcare.</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
