document.addEventListener('click', e => { const b=e.target.closest('button[data-viewer]'); if(b) document.getElementById(b.dataset.viewer).src=b.dataset.model; });
