// Simple markdown rendering for completed session views
(function() {
  document.querySelectorAll('.markdown-content').forEach(el => {
    const raw = el.textContent;
    if (!raw || el.dataset.rendered) return;
    
    const html = raw
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/gs, '<ul>$&</ul>')
      .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
      .replace(/\n{2,}/g, '</p><p>')
      .replace(/^(?!<[hulo])(.+)$/gm, '<p>$1</p>')
      .replace(/CONFIDENCE:\s*[\d.]+/gi, '');
    
    el.innerHTML = html;
    el.dataset.rendered = 'true';
  });
})();
