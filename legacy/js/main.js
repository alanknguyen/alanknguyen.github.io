// Theme toggle
(function () {
  var toggle = document.getElementById('themeToggle');
  var html = document.documentElement;
  var stored = localStorage.getItem('theme');

  if (stored) {
    html.setAttribute('data-theme', stored);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    html.setAttribute('data-theme', 'dark');
  }

  updateIcon();

  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateIcon();
    });
  }

  function updateIcon() {
    if (!toggle) return;
    var theme = html.getAttribute('data-theme');
    toggle.innerHTML = theme === 'dark' ? '&#9788; Theme' : '&#9790; Theme';
  }
})();

// Mobile sidebar toggle
(function () {
  var hamburger = document.getElementById('hamburger');
  var sidebar = document.getElementById('sidebar');

  if (hamburger && sidebar) {
    hamburger.addEventListener('click', function () {
      sidebar.classList.toggle('collapsed');
    });
  }
})();
