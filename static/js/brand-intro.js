(() => {
  const root = document.documentElement;
  const intro = document.querySelector('[data-brand-intro]');
  if (!intro || !root.classList.contains('brand-intro-pending')) return;

  const word = intro.querySelector('[data-brand-intro-word]');
  const skip = intro.querySelector('[data-brand-intro-skip]');
  const brand = (intro.dataset.brandName || '').trim() || 'D.A.R.C.Y.';
  let closed = false;

  const characters = typeof Intl !== 'undefined' && Intl.Segmenter
    ? [...new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(brand)].map(item => item.segment)
    : Array.from(brand);

  if (characters.length > 9) word.classList.add('is-long');
  if (characters.length > 15) word.classList.add('is-extra-long');

  characters.forEach((character, index) => {
    const letter = document.createElement('span');
    if (/\s/.test(character)) {
      letter.className = 'brand-intro__space';
      letter.setAttribute('aria-hidden', 'true');
    } else {
      letter.className = 'brand-intro__letter';
      letter.textContent = character;
      letter.dataset.letter = character;
      letter.style.setProperty('--letter-delay', `${1220 + (index * 58)}ms`);
      letter.style.setProperty('--accent-delay', `${1110 + (index * 52)}ms`);
      letter.style.setProperty('--drift', `${(index - ((characters.length - 1) / 2)) * 12}px`);
      letter.style.setProperty('--tilt', `${(index - ((characters.length - 1) / 2)) * 1.8}deg`);
    }
    word.appendChild(letter);
  });

  const finish = () => {
    if (closed) return;
    closed = true;
    intro.classList.add('is-leaving');
    try { window.sessionStorage.setItem('darcy-brand-intro-seen', '1'); } catch (error) { /* Navegación privada. */ }
    window.setTimeout(() => {
      root.classList.remove('brand-intro-pending');
      intro.remove();
    }, 760);
  };

  skip?.addEventListener('click', finish);
  window.setTimeout(finish, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 250 : 3500);
})();
