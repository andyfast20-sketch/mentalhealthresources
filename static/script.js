const tags = Array.from(document.querySelectorAll('.tag'));
const cards = Array.from(document.querySelectorAll('.resource-card'));
const resetBtn = document.getElementById('filter-reset');
const darkToggle = document.getElementById('dark-toggle');

function applyFilter(tag) {
  cards.forEach((card) => {
    const hasTag = card.dataset.tags.split(' ').includes(tag);
    card.classList.toggle('hidden', !hasTag);
  });
}

function resetFilters() {
  cards.forEach((card) => card.classList.remove('hidden'));
  tags.forEach((tag) => tag.classList.remove('active'));
}

tags.forEach((tagBtn) => {
  tagBtn.addEventListener('click', () => {
    const isActive = tagBtn.classList.contains('active');
    resetFilters();
    if (!isActive) {
      tagBtn.classList.add('active');
      applyFilter(tagBtn.dataset.tag);
    }
  });
});

resetBtn?.addEventListener('click', resetFilters);

darkToggle?.addEventListener('click', () => {
  document.body.classList.toggle('glow');
  darkToggle.textContent = document.body.classList.contains('glow') ? 'Night Mode' : 'Glow Mode';
});

// Smooth scroll for in-page anchors
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', function (e) {
    if (this.getAttribute('href') === '#') return;
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    target?.scrollIntoView({ behavior: 'smooth' });
  });
});

// micro interaction: show subtle pulse on cards
cards.forEach((card) => {
  card.addEventListener('mouseenter', () => card.classList.add('pulse'));
  card.addEventListener('mouseleave', () => card.classList.remove('pulse'));
});
