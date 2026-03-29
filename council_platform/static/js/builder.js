// Council Builder — agent selection + save
(function() {
  const selectedAgents = new Set();
  const agentEls = document.querySelectorAll('.builder-agent');
  const selectedList = document.getElementById('selected-agents');
  const agentIdsInput = document.getElementById('agent-ids-input');
  const saveBtn = document.getElementById('save-council-btn');
  const form = document.getElementById('builder-form');
  
  if (!agentEls.length) return;
  
  agentEls.forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.agentId;
      if (selectedAgents.has(id)) {
        selectedAgents.delete(id);
        el.classList.remove('selected');
      } else {
        if (selectedAgents.size >= 7) {
          alert('Maximum 7 agents per council');
          return;
        }
        selectedAgents.add(id);
        el.classList.add('selected');
      }
      updateSelectedList();
    });
  });
  
  function updateSelectedList() {
    if (!selectedList) return;
    const ids = Array.from(selectedAgents);
    selectedList.innerHTML = ids.map(id => {
      const name = id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      return `<span class="selected-agent-chip">${name} <span class="remove" data-id="${id}">×</span></span>`;
    }).join('');
    
    if (agentIdsInput) agentIdsInput.value = JSON.stringify(ids);
    
    // Bind remove buttons
    selectedList.querySelectorAll('.remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        selectedAgents.delete(id);
        document.querySelector(`.builder-agent[data-agent-id="${id}"]`)?.classList.remove('selected');
        updateSelectedList();
      });
    });
  }
  
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (selectedAgents.size < 2) {
        alert('Select at least 2 agents');
        return;
      }
      
      const formData = new FormData(form);
      formData.set('agent_ids', JSON.stringify(Array.from(selectedAgents)));
      
      try {
        const resp = await fetch('/builder/save', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.success) {
          alert('Council saved! You can now use it from the home page.');
          window.location.href = '/';
        }
      } catch (err) {
        alert('Error saving council: ' + err.message);
      }
    });
  }
})();
