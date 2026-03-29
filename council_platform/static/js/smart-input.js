// Smart Input — intent classification + council selector
(function() {
  const input = document.getElementById('smart-input');
  const intentRow = document.getElementById('intent-suggestion');
  const intentText = document.getElementById('intent-text');
  const intentAccept = document.getElementById('intent-accept');
  const options = document.querySelectorAll('.council-option');
  
  if (!input) return;
  
  let debounce = null;
  
  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(classifyIntent, 400);
  });
  
  async function classifyIntent() {
    const q = input.value.trim();
    if (q.length < 10) {
      if (intentRow) intentRow.style.display = 'none';
      return;
    }
    
    try {
      const resp = await fetch(`/classify-intent?q=${encodeURIComponent(q)}`);
      const data = await resp.json();
      
      if (data.intent && data.intent !== 'unknown') {
        const labels = {
          selves: '🪞 Council of Selves — inner dialogue about a personal decision',
          idea: '⚔️ Idea Council — stress-test a formed proposal',
          innovation: '🔬 Innovation Lab — explore possibilities in a theme',
        };
        
        if (intentRow) {
          intentRow.style.display = 'flex';
          intentText.textContent = 'Suggested: ' + (labels[data.intent] || data.intent);
        }
        
        // Auto-select
        selectCouncil(data.intent);
      }
    } catch (e) {
      // Silently ignore classification errors
    }
  }
  
  function selectCouncil(type) {
    options.forEach(opt => {
      const radio = opt.querySelector('input[type="radio"]');
      if (radio && radio.value === type) {
        radio.checked = true;
        opt.classList.add('selected');
      } else {
        opt.classList.remove('selected');
      }
    });
  }
  
  // Click handling for council options
  options.forEach(opt => {
    opt.addEventListener('click', () => {
      options.forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
    });
  });
  
  if (intentAccept) {
    intentAccept.addEventListener('click', () => {
      // Already auto-selected on classification
      input.focus();
    });
  }
  
  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  });
})();
