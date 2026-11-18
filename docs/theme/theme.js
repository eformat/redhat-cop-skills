(function() {
  var btn = document.getElementById('themeToggle');
  var root = document.documentElement;
  function stored() { try { return localStorage.getItem('rhcop-theme'); } catch (e) { return null; } }
  function set(theme, persist) {
    if (theme) root.setAttribute('data-theme', theme);
    else root.removeAttribute('data-theme');
    btn.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    if (persist) { try { localStorage.setItem('rhcop-theme', theme || ''); } catch (e) {} }
  }
  var saved = stored();
  if (saved === 'dark' || saved === 'light') set(saved, false);
  btn.addEventListener('click', function() {
    set(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark', true);
  });
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc li a'));
  var secs = links.map(function(a) { return document.querySelector(a.getAttribute('href')); });
  function spy() {
    var y = window.scrollY + 80, i = secs.length - 1;
    while (i > 0 && (!secs[i] || secs[i].offsetTop > y)) i--;
    links.forEach(function(a, j) { a.classList.toggle('active', j === i && !!secs[j]); });
  }
  window.addEventListener('scroll', spy, { passive: true }); spy();
})();
