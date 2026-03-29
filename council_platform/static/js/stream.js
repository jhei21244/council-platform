// SSE Streaming — real-time agent completions
(function() {
  if (typeof SESSION_ID === 'undefined') return;
  
  const grid = document.getElementById('agents-grid');
  const statusText = document.getElementById('stream-status-text');
  const statusBar = document.getElementById('stream-status');
  const synthesisSection = document.getElementById('synthesis-section');
  const synthesisContent = document.getElementById('synthesis-content');
  const phaseMarkers = document.getElementById('phase-markers');
  
  const agentCards = {};
  const agentContent = {};
  
  const source = new EventSource(`/stream/${SESSION_ID}`);
  
  source.addEventListener('agent_started', (e) => {
    const data = JSON.parse(e.data);
    const id = data.agent_id;
    
    if (statusText) statusText.textContent = `${id.replace(/-/g, ' ')} is thinking...`;
    
    // Create or update card
    let card = agentCards[id];
    if (!card) {
      card = createAgentCard(id, data);
      grid.appendChild(card);
      agentCards[id] = card;
    }
    card.className = 'agent-card card-thinking';
    agentContent[id] = '';
  });
  
  source.addEventListener('agent_token', (e) => {
    const data = JSON.parse(e.data);
    const id = data.agent_id;
    
    if (!agentContent[id]) agentContent[id] = '';
    agentContent[id] += data.token;
    
    const contentEl = agentCards[id]?.querySelector('.agent-card-content');
    if (contentEl) {
      contentEl.textContent = agentContent[id];
    }
  });
  
  source.addEventListener('agent_completed', (e) => {
    const data = JSON.parse(e.data);
    const id = data.agent_id;
    const card = agentCards[id];
    
    if (card) {
      card.className = 'agent-card card-complete';
      
      // Update content
      const contentEl = card.querySelector('.agent-card-content');
      if (contentEl) contentEl.innerHTML = simpleMarkdown(data.content);
      
      // Add confidence bar
      if (data.confidence != null) {
        const pct = Math.round(data.confidence * 100);
        const barWrapper = card.querySelector('.confidence-bar-wrapper');
        const barLabel = card.querySelector('.confidence-label');
        if (barWrapper) {
          barWrapper.innerHTML = `<div class="confidence-bar" style="width:${pct}%;background:${COUNCIL_ACCENT}"></div>`;
        }
        if (barLabel) barLabel.textContent = `${pct}% confidence`;
      }
      
      // Add cost
      if (data.cost_usd > 0) {
        const footer = card.querySelector('.agent-card-footer');
        if (footer) footer.innerHTML = `<span class="agent-cost">$${data.cost_usd.toFixed(4)}</span>`;
      }
      
      // Model indicator
      const indicators = card.querySelector('.agent-card-indicators');
      if (indicators && data.model_used) {
        const sym = data.model_used.includes('gemini') ? '◈' : '◉';
        indicators.innerHTML = `<span class="model-indicator" title="${data.model_used}">${sym}</span>`;
      }
    }
  });
  
  source.addEventListener('phase_completed', (e) => {
    const data = JSON.parse(e.data);
    if (phaseMarkers) {
      const marker = document.createElement('div');
      marker.className = 'phase-marker';
      marker.innerHTML = `<span>Phase ${data.phase} complete${data.phase_name ? ': ' + data.phase_name : ''}</span>`;
      marker.style.cssText = 'text-align:center;padding:1rem 0;font-size:0.8rem;color:var(--outline);border-top:1px solid var(--outline-variant);margin:1rem 0;';
      phaseMarkers.appendChild(marker);
    }
    if (statusText) statusText.textContent = `Phase ${data.phase} complete. ${data.phase_name || 'Continuing...'}`;
  });
  
  source.addEventListener('synthesis_started', () => {
    if (statusText) statusText.textContent = 'Synthesising...';
    if (synthesisSection) synthesisSection.style.opacity = '1';
    if (synthesisContent) synthesisContent.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  });
  
  source.addEventListener('synthesis_token', (e) => {
    const data = JSON.parse(e.data);
    if (!window._synthContent) window._synthContent = '';
    window._synthContent += data.token;
    if (synthesisContent) synthesisContent.textContent = window._synthContent;
  });
  
  source.addEventListener('synthesis_completed', (e) => {
    const data = JSON.parse(e.data);
    if (synthesisContent) synthesisContent.innerHTML = simpleMarkdown(data.content);
    if (statusText) statusText.textContent = 'Deliberation complete';
  });
  
  source.addEventListener('session_completed', () => {
    source.close();
    if (statusBar) statusBar.style.display = 'none';
    // Reload to show final state with chain buttons
    setTimeout(() => window.location.reload(), 500);
  });
  
  source.addEventListener('error', (e) => {
    const data = e.data ? JSON.parse(e.data) : {};
    if (statusText) statusText.textContent = 'Error: ' + (data.message || 'Connection lost');
    source.close();
  });
  
  source.onerror = () => {
    if (statusText) statusText.textContent = 'Connection lost. Refresh to see results.';
    source.close();
  };
  
  function createAgentCard(id, data) {
    const card = document.createElement('div');
    card.className = 'agent-card card-waiting';
    card.dataset.agentId = id;
    
    const name = id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const providerSym = (data.provider === 'google') ? '◈' : '◉';
    
    card.innerHTML = `
      <div class="agent-card-header">
        <div class="agent-card-icon">🤖</div>
        <div class="agent-card-meta">
          <div class="agent-card-name">${name}</div>
          <div class="agent-card-function">${data.provider || 'agent'}</div>
        </div>
        <div class="agent-card-indicators">
          <span class="model-indicator" title="${data.model || ''}">${providerSym}</span>
          ${data.phase > 1 ? `<span class="phase-badge">Ph.${data.phase}</span>` : ''}
        </div>
      </div>
      <div class="confidence-bar-wrapper"><div class="confidence-bar" style="width:0"></div></div>
      <div class="confidence-label"></div>
      <div class="agent-card-content">
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>
      <div class="agent-card-footer"></div>
    `;
    return card;
  }
  
  function simpleMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
      .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
      .replace(/\n{2,}/g, '</p><p>')
      .replace(/^(?!<[hulo])(.+)$/gm, '<p>$1</p>')
      .replace(/CONFIDENCE:\s*[\d.]+/g, '');  // Strip confidence from display
  }
})();
