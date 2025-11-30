const calmingCompleteButtons = Array.from(document.querySelectorAll('[data-calming-complete]'));

function updateCalmingCounts(slug, newCount) {
  document.querySelectorAll(`[data-calming-count="${slug}"]`).forEach((node) => {
    node.textContent = newCount;
  });
}

function handleCalmingComplete(button) {
  if (!button) return;

  const slug = button.dataset.calmingSlug;
  if (!slug) return;

  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = 'Logged';

  fetch(`/calming-tools/${slug}/complete`, { method: 'POST' })
    .then((response) => response.json())
    .then((data) => {
      if (!data?.success) return;
      updateCalmingCounts(slug, data.completed_count);
    })
    .catch(() => {})
    .finally(() => {
      button.textContent = originalText;
      button.disabled = false;
    });
}

calmingCompleteButtons.forEach((button) => {
  button.addEventListener('click', () => handleCalmingComplete(button));
});
