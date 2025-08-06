import { useEffect } from 'react';

export function Shortcuts() {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Focus search on "/" key
      if (e.key === '/') { 
        e.preventDefault(); 
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
          searchInput.focus();
        }
      }
      // TODO: Add queue/draft shortcuts when we have focused row logic
      // if (e.key === 'q') queueOrUnqueueFocusedRow?.();
      // if (e.key === 'd') draftFocusedRow?.();
      // if (e.key === '?') openHelpModal();
    };
    
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return null; // This component doesn't render anything
}
