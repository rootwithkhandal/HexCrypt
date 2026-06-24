import { useState, useEffect, useRef } from 'react';

function App() {
  const [activeTab, setActiveTab] = useState('encrypt'); // encrypt, steg, hash
  const [mode, setMode] = useState('symmetric');
  const [inputText, setInputText] = useState('');
  const [keyInput, setKeyInput] = useState('');
  const [ttl, setTtl] = useState('');
  const [output, setOutput] = useState('System waiting for input payload...');
  const [logs, setLogs] = useState([]);
  const [showToast, setShowToast] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Steganography State
  const [stegCarrier, setStegCarrier] = useState(null);
  const [stegPayload, setStegPayload] = useState(null);

  // Hashing State
  const [hashFile, setHashFile] = useState(null);
  const [hashResults, setHashResults] = useState(null);
  const [verifyHash, setVerifyHash] = useState('');

  useEffect(() => {
    addLog('Kernel initialized');
  }, []);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev, `[LOG] ${time} ${msg}`]);
  };

  const handleGenerateKey = async () => {
    try {
      const res = await fetch('/api/keygen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      const data = await res.json();
      if (data.key) {
        setKeyInput(data.key);
      } else if (data.priv_key && data.pub_key) {
        alert(`Public Key (For Encrypting):\n${data.pub_key}\n\nPrivate Key (For Decrypting):\n${data.priv_key}\n\nPlease copy your Private Key to decrypt later!`);
        setKeyInput(data.pub_key); // Auto-fill the public key so they can encrypt
      }
      addLog(`Generated new ${mode} key`);
    } catch (e) {
      addLog(`Key generation failed: ${e.message}`);
    }
  };

  const handleProcess = async (operation) => {
    if (!inputText) return;
    setIsProcessing(true);
    addLog(`Starting ${operation} process...`);
    
    try {
      const res = await fetch(`/api/${operation}/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: inputText, 
          key: keyInput, 
          ttl: ttl ? parseInt(ttl, 10) : null 
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        setOutput(data.result);
        addLog(`${operation} completed successfully`);
      } else {
        const errMsg = data.detail || data.error || 'Invalid key or corrupted data';
        setOutput(`ERROR: ${errMsg}`);
        addLog(`Process failed`);
      }
    } catch (e) {
      setOutput(`NETWORK ERROR: ${e.message}`);
      addLog(`Network error`);
    } finally {
      setIsProcessing(false);
    }
  };

  const copyOutput = () => {
    navigator.clipboard.writeText(output);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2000);
  };

  const handleStegEmbed = async () => {
    if (!stegCarrier || !stegPayload) return;
    setIsProcessing(true);
    addLog('Starting steganography embed process...');
    const formData = new FormData();
    formData.append('carrier', stegCarrier);
    formData.append('payload', stegPayload);

    try {
      const res = await fetch('/api/steg/embed', { method: 'POST', body: formData });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `embedded_${stegCarrier.name}`;
        a.click();
        addLog('Steganography embed completed');
      } else {
        const data = await res.json();
        alert(`Error: ${data.detail}`);
        addLog('Steganography embed failed');
      }
    } catch (e) {
      alert(`Network error: ${e.message}`);
      addLog('Network error during steg embed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStegExtract = async () => {
    if (!stegCarrier) return;
    setIsProcessing(true);
    addLog('Starting steganography extract process...');
    const formData = new FormData();
    formData.append('carrier', stegCarrier);

    try {
      const res = await fetch('/api/steg/extract', { method: 'POST', body: formData });
      if (res.ok) {
        const blob = await res.blob();
        
        let filename = 'extracted_payload.bin';
        const disposition = res.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
          const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          const matches = filenameRegex.exec(disposition);
          if (matches != null && matches[1]) { 
            filename = matches[1].replace(/['"]/g, '');
          }
        }
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        addLog(`Steganography extract completed: ${filename}`);
      } else {
        const data = await res.json();
        alert(`Error: ${data.detail}`);
        addLog('Steganography extract failed');
      }
    } catch (e) {
      alert(`Network error: ${e.message}`);
      addLog('Network error during steg extract');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHash = async () => {
    if (!hashFile) return;
    setIsProcessing(true);
    addLog(`Calculating hashes for ${hashFile.name}...`);
    const formData = new FormData();
    formData.append('file', hashFile);

    try {
      const res = await fetch('/api/hash', { method: 'POST', body: formData });
      if (res.ok) {
        const data = await res.json();
        setHashResults(data);
        addLog(`Hashes calculated for ${hashFile.name}`);
      } else {
        const data = await res.json();
        alert(`Error: ${data.detail}`);
        addLog('Hashing failed');
      }
    } catch (e) {
      alert(`Network error: ${e.message}`);
      addLog('Network error during hashing');
    } finally {
      setIsProcessing(false);
    }
  };

  let hashMatch = null;
  if (verifyHash && hashResults) {
    const target = verifyHash.toLowerCase().trim();
    if (target === hashResults.MD5.toLowerCase() || target === hashResults.SHA1.toLowerCase() || target === hashResults.SHA256.toLowerCase() || target === hashResults.SHA512.toLowerCase()) {
      hashMatch = true;
    } else {
      hashMatch = false;
    }
  }

  return (
    <div className="min-h-screen selection:bg-primary-fixed-dim/30 selection:text-primary-fixed-dim pb-32">
      <header className="fixed top-0 w-full z-50 bg-surface/40 backdrop-blur-xl border-b border-white/10">
        <div className="flex items-center justify-between px-margin-mobile h-16 w-full max-w-container-max mx-auto">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary-fixed-dim" style={{fontVariationSettings: "'FILL' 1"}}>shield_lock</span>
            <h1 className="font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tighter text-primary-fixed-dim">HexCrypt</h1>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => setActiveTab('encrypt')} className={`font-label-xs text-label-xs uppercase tracking-widest ${activeTab === 'encrypt' ? 'text-primary-fixed-dim border-b border-primary-fixed-dim' : 'text-outline hover:text-white'}`}>Encrypt/Decrypt</button>
            <button onClick={() => setActiveTab('steg')} className={`font-label-xs text-label-xs uppercase tracking-widest ${activeTab === 'steg' ? 'text-primary-fixed-dim border-b border-primary-fixed-dim' : 'text-outline hover:text-white'}`}>Steganography</button>
            <button onClick={() => setActiveTab('hash')} className={`font-label-xs text-label-xs uppercase tracking-widest ${activeTab === 'hash' ? 'text-primary-fixed-dim border-b border-primary-fixed-dim' : 'text-outline hover:text-white'}`}>Hash & Integrity</button>
          </div>
        </div>
      </header>

      <main className="pt-24 px-margin-mobile max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-gutter relative z-10">
        
        {activeTab === 'encrypt' && (
          <>
            <div className="lg:col-span-12 mb-4">
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                  <h2 className="font-headline-xl text-[40px] font-bold text-primary mb-1">Secure Encrypt/Decrypt</h2>
                  <p className="font-body-md text-outline">Manage sensitive data packets with military-grade standards.</p>
                </div>
                
                <div className="flex p-1 bg-surface-container-low border border-white/5 rounded-xl w-fit">
                  <button 
                    onClick={() => setMode('symmetric')}
                    className={`px-6 py-2 rounded-lg font-label-xs text-label-xs transition-all duration-300 ${mode === 'symmetric' ? 'bg-primary-fixed-dim text-on-primary-fixed' : 'text-outline hover:text-primary'}`}>
                    Symmetric
                  </button>
                  <button 
                    onClick={() => setMode('asymmetric')}
                    className={`px-6 py-2 rounded-lg font-label-xs text-label-xs transition-all duration-300 ${mode === 'asymmetric' ? 'bg-primary-fixed-dim text-on-primary-fixed' : 'text-outline hover:text-primary'}`}>
                    Asymmetric
                  </button>
                </div>
              </div>
            </div>

            <div className="lg:col-span-7 space-y-gutter">
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <div className="flex items-center justify-between">
                  <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">data_object</span>
                    Payload Data
                  </label>
                  <span className="font-label-xs text-label-xs text-outline opacity-60">UTF-8 / BASE64</span>
                </div>
                <textarea 
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  className="w-full h-48 bg-surface-container-lowest border border-white/10 rounded-lg p-4 font-code-sm text-code-sm text-on-surface-variant focus:border-primary-fixed-dim resize-none transition-all placeholder:opacity-30" 
                  placeholder="Enter sensitive data here for processing..."></textarea>
              </div>

              <div className="glass-panel p-6 rounded-xl space-y-6">
                <div className="flex items-center justify-between">
                  <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">vpn_key</span>
                    Key Management
                  </label>
                  <button onClick={handleGenerateKey} className="font-label-xs text-label-xs text-primary-fixed-dim border border-primary-fixed-dim/30 px-3 py-1 rounded hover:bg-primary-fixed-dim/10 transition-colors flex items-center gap-2 active:scale-95">
                    <span className="material-symbols-outlined text-xs">refresh</span>
                    {mode === 'symmetric' ? 'Generate Key' : 'Generate X25519'}
                  </button>
                </div>
                <div className="space-y-4">
                  <div className="relative group">
                    <input 
                      type="text"
                      value={keyInput}
                      onChange={e => setKeyInput(e.target.value)}
                      className="w-full h-12 bg-surface-container-lowest border border-white/10 rounded-lg p-4 pr-12 font-code-sm text-code-sm text-on-surface-variant transition-all" 
                      placeholder={mode === 'symmetric' ? "Paste key or passphrase..." : "Paste Recipient PubKey or Your PrivKey..."} />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline group-focus-within:text-primary-fixed-dim">key_visualizer</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="font-label-xs text-label-xs text-outline opacity-60">TTL (Time To Live)</label>
                      <div className="flex items-center bg-surface-container-lowest border border-white/10 rounded-lg overflow-hidden h-12">
                        <input 
                          type="number" 
                          value={ttl}
                          onChange={e => setTtl(e.target.value)}
                          placeholder="e.g. 60"
                          className="w-full bg-transparent border-none font-code-sm text-code-sm text-on-surface px-4 focus:ring-0" />
                        <span className="bg-surface-container-high px-4 h-full flex items-center font-label-xs text-label-xs text-outline border-l border-white/10">SEC</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <button 
                  onClick={() => handleProcess('encrypt')}
                  className="flex-1 h-14 bg-primary-container text-on-primary-container font-headline-lg-mobile text-[18px] font-bold rounded-xl active:scale-[0.98] transition-all hover:brightness-110 flex items-center justify-center gap-3 neon-glow-primary group">
                  <span className="material-symbols-outlined group-hover:rotate-180 transition-transform duration-500">lock</span>
                  Encrypt
                </button>
                <button 
                  onClick={() => handleProcess('decrypt')}
                  className="flex-1 h-14 bg-surface-container-high border border-white/10 text-primary-fixed-dim font-headline-lg-mobile text-[18px] font-bold rounded-xl active:scale-[0.98] transition-all hover:bg-surface-container-highest flex items-center justify-center gap-3 group">
                  <span className="material-symbols-outlined group-hover:rotate-180 transition-transform duration-500">lock_open</span>
                  Decrypt
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'steg' && (
          <div className="lg:col-span-7 space-y-gutter">
            <div className="mb-4">
              <h2 className="font-headline-xl text-[40px] font-bold text-primary mb-1">Steganography</h2>
              <p className="font-body-md text-outline">Hide encrypted payloads inside standard PNG images.</p>
            </div>
            
            <div className="glass-panel p-6 rounded-xl space-y-6">
              <div className="space-y-2">
                <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest flex items-center gap-2">Carrier Image (PNG)</label>
                <input type="file" accept=".png" onChange={e => setStegCarrier(e.target.files[0])} className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2 text-sm text-outline" />
              </div>
              <div className="space-y-2">
                <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest flex items-center gap-2">Payload File (To Embed)</label>
                <input type="file" onChange={e => setStegPayload(e.target.files[0])} className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2 text-sm text-outline" />
              </div>
            </div>

            <div className="flex gap-4">
                <button onClick={handleStegEmbed} className="flex-1 h-14 bg-primary-container text-on-primary-container font-headline-lg-mobile text-[18px] font-bold rounded-xl active:scale-[0.98] transition-all hover:brightness-110 flex items-center justify-center gap-3 neon-glow-primary group">
                  <span className="material-symbols-outlined">image</span>
                  Embed Payload
                </button>
                <button onClick={handleStegExtract} className="flex-1 h-14 bg-surface-container-high border border-white/10 text-primary-fixed-dim font-headline-lg-mobile text-[18px] font-bold rounded-xl active:scale-[0.98] transition-all hover:bg-surface-container-highest flex items-center justify-center gap-3 group">
                  <span className="material-symbols-outlined">search</span>
                  Extract Payload
                </button>
            </div>
          </div>
        )}

        {activeTab === 'hash' && (
          <div className="lg:col-span-7 space-y-gutter">
            <div className="mb-4">
              <h2 className="font-headline-xl text-[40px] font-bold text-primary mb-1">Hash & Integrity</h2>
              <p className="font-body-md text-outline">Verify file authenticity and integrity.</p>
            </div>

            <div className="glass-panel p-6 rounded-xl space-y-6">
              <div className="space-y-2">
                <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest flex items-center gap-2">Target File</label>
                <input type="file" onChange={e => setHashFile(e.target.files[0])} className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2 text-sm text-outline" />
              </div>
              <button onClick={handleHash} className="w-full h-12 bg-primary-container text-on-primary-container font-bold rounded-lg hover:brightness-110">
                Calculate Hashes
              </button>
            </div>

            {hashResults && (
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <h3 className="font-bold text-primary-fixed-dim">Results for {hashResults.filename}</h3>
                {['MD5', 'SHA1', 'SHA256', 'SHA512'].map(algo => (
                  <div key={algo}>
                    <label className="text-xs text-outline font-bold">{algo}</label>
                    <input readOnly value={hashResults[algo]} className="w-full bg-surface-container-lowest border border-white/10 rounded p-2 text-xs font-code-sm" />
                  </div>
                ))}

                <div className="pt-4 border-t border-white/10">
                  <label className="text-xs text-outline font-bold">Verify Against Known Hash:</label>
                  <input type="text" placeholder="Paste hash here..." value={verifyHash} onChange={e => setVerifyHash(e.target.value)} className="w-full bg-surface-container-lowest border border-white/10 rounded p-2 text-xs mt-1 focus:border-primary-fixed-dim" />
                  {verifyHash && (
                    <div className={`mt-2 p-2 rounded text-sm font-bold ${hashMatch ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                      {hashMatch ? '✅ MATCH' : '❌ NO MATCH'}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="lg:col-span-5 space-y-gutter">
          <div className="glass-panel p-6 rounded-xl h-full flex flex-col min-h-[500px]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-error' : 'bg-primary-fixed-dim'} animate-pulse`}></div>
                <label className="font-label-xs text-label-xs text-primary-fixed-dim uppercase tracking-widest">Process Output / Logs</label>
              </div>
              <button onClick={copyOutput} className="p-2 text-outline hover:text-primary transition-colors flex items-center gap-1 active:scale-90">
                <span className="material-symbols-outlined text-sm">content_copy</span>
                <span className="text-[10px] uppercase font-bold">Copy</span>
              </button>
            </div>
            
            <div className="flex-grow bg-[#0c0e12] border border-white/5 rounded-lg p-4 font-code-sm text-code-sm text-primary-fixed-dim/80 overflow-y-auto no-scrollbar relative max-h-[600px]">
              <div className="mb-4 whitespace-pre-wrap break-all text-[13px]">{output}</div>
              
              <div className="space-y-1 mt-8 border-t border-white/5 pt-4">
                {logs.map((log, i) => (
                  <p key={i} className="text-[11px] text-outline/50 font-code-sm">{log}</p>
                ))}
              </div>
              
              {showToast && (
                <div className="absolute bottom-4 right-4 bg-surface-container-highest border border-primary-fixed-dim/40 rounded px-3 py-1 flex items-center gap-2 transition-all duration-300">
                  <span className="material-symbols-outlined text-primary-fixed-dim text-sm" style={{fontVariationSettings: "'FILL' 1"}}>check_circle</span>
                  <span className="text-[10px] font-bold text-primary uppercase">Copied to buffer</span>
                </div>
              )}
            </div>

            {isProcessing && (
              <div className="mt-4 p-4 border border-white/5 bg-surface-container-low rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-label-xs text-label-xs text-outline">Processing</span>
                </div>
                <div className="h-1 bg-surface-container-highest rounded-full scanning-bar"></div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
