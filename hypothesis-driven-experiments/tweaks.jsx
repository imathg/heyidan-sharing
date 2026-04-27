// tweaks.jsx — typography & layout tweaks for the static site
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "fontFamily": "serif",
  "fontSize": 17,
  "measure": 68,
  "accent": "#1f3a5f"
}/*EDITMODE-END*/;

function applyTweaks(t) {
  const root = document.documentElement;
  if (t.fontFamily === 'sans') {
    root.style.setProperty('--serif', 'var(--sans-en), var(--sans-cn)');
  } else {
    root.style.removeProperty('--serif');
  }
  root.style.setProperty('--fs-body', t.fontSize + 'px');
  root.style.setProperty('--measure', t.measure + 'ch');
  root.style.setProperty('--accent', t.accent);
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  React.useEffect(() => { applyTweaks(t); }, [t]);
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="Typography" />
      <TweakRadio label="Family" value={t.fontFamily}
        options={[{label:'Serif',value:'serif'},{label:'Sans',value:'sans'}]}
        onChange={(v) => setTweak('fontFamily', v)} />
      <TweakSlider label="Size" value={t.fontSize} min={14} max={20} step={1} unit="px"
        onChange={(v) => setTweak('fontSize', v)} />
      <TweakSection label="Layout" />
      <TweakSlider label="Measure" value={t.measure} min={56} max={80} step={2} unit="ch"
        onChange={(v) => setTweak('measure', v)} />
      <TweakSection label="Accent" />
      <TweakColor label="Color" value={t.accent}
        onChange={(v) => setTweak('accent', v)} />
    </TweaksPanel>
  );
}

const mount = document.createElement('div');
document.body.appendChild(mount);
ReactDOM.createRoot(mount).render(<App />);
