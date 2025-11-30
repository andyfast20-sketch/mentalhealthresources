const tags = Array.from(document.querySelectorAll('.tag'));
const cards = Array.from(document.querySelectorAll('.resource-card'));
const resetBtn = document.getElementById('filter-reset');
const sliderTrack = document.querySelector('[data-charity-track]');
const sliderProgress = document.querySelector('[data-slide-progress]');
const sliderPrev = document.querySelector('[data-slide-prev]');
const sliderNext = document.querySelector('[data-slide-next]');
const sliderWindow = document.querySelector('.slider-window');
const dropdownTriggers = Array.from(document.querySelectorAll('[data-dropdown-toggle]'));
const showCharitiesBtn = document.querySelector('[data-show-charities]');
const charityModal = document.querySelector('[data-charity-modal]');
const modalClose = document.querySelector('[data-modal-close]');
const bookTrack = document.querySelector('[data-book-track]');
const bookPrev = document.querySelector('[data-book-prev]');
const bookNext = document.querySelector('[data-book-next]');
const bookModal = document.querySelector('[data-book-modal]');
const bookModalTitle = document.querySelector('[data-book-modal-title]');
const bookModalAuthor = document.querySelector('[data-book-modal-author]');
const bookModalDescription = document.querySelector('[data-book-modal-description]');
const bookModalCover = document.querySelector('[data-book-modal-cover]');
const bookModalCoverWrapper = document.querySelector('[data-book-modal-cover-wrapper]');
const bookModalCoverFallback = document.querySelector('[data-book-modal-cover-fallback]');
const bookModalLink = document.querySelector('[data-book-modal-link]');
const bookTriggerButtons = Array.from(document.querySelectorAll('[data-book-trigger]'));
const bookCards = Array.from(document.querySelectorAll('.book-card[data-book-index]'));
const bookModalCloseButtons = Array.from(document.querySelectorAll('[data-book-modal-close]'));
const adminBookModal = document.querySelector('[data-admin-book-modal]');
const adminBookForm = document.querySelector('[data-admin-book-form]');
const adminBookCloseButtons = Array.from(document.querySelectorAll('[data-admin-book-modal-close]'));
const adminBookEditTriggers = Array.from(document.querySelectorAll('[data-admin-book-edit-trigger]'));
const crisisVolume = document.querySelector('[data-crisis-volume]');
const crisisVolumeValue = document.querySelector('[data-crisis-volume-value]');
let slideIndex = 0;
let slideWidth = 0;
let crisisPlayer;
let activeBookTrigger = null;
let activeAdminTrigger = null;
const trackedScrollBooks = new Set();

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

dropdownTriggers.forEach((trigger) => {
  const menu = trigger.closest('.nav-dropdown');
  trigger.addEventListener('click', (event) => {
    event.preventDefault();
    const isOpen = menu?.classList.toggle('is-open');
    trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
});

dropdownTriggers.forEach((trigger) => {
  const menu = trigger.closest('.nav-dropdown');
  menu?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    });
  });
});

document.addEventListener('click', (event) => {
  dropdownTriggers.forEach((trigger) => {
    const menu = trigger.closest('.nav-dropdown');
    if (menu && !menu.contains(event.target)) {
      menu.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    }
  });
});

function setSlide(index) {
  if (!sliderTrack) return;
  const slides = Array.from(sliderTrack.children);
  if (!slides.length) return;
  slideIndex = (index + slides.length) % slides.length;
  slideWidth = sliderWindow?.getBoundingClientRect().width || slides[0].getBoundingClientRect().width;
  sliderTrack.style.transform = `translateX(-${slideIndex * slideWidth}px)`;
  const progressValue = ((slideIndex + 1) / slides.length) * 100;
  if (sliderProgress) sliderProgress.style.width = `${progressValue}%`;
  slides.forEach((slide, idx) => {
    slide.classList.toggle('is-active', idx === slideIndex);
  });
}

function initSlider() {
  if (!sliderTrack) return;
  setSlide(0);
  sliderPrev?.addEventListener('click', () => setSlide(slideIndex - 1));
  sliderNext?.addEventListener('click', () => setSlide(slideIndex + 1));
  window.addEventListener('resize', () => setSlide(slideIndex));

  let startX = 0;
  sliderTrack.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
  });
  sliderTrack.addEventListener('touchend', (e) => {
    const delta = e.changedTouches[0].clientX - startX;
    if (Math.abs(delta) > 40) {
      setSlide(slideIndex + (delta < 0 ? 1 : -1));
    }
  });
}

initSlider();

function scrollBooks(direction = 1) {
  if (!bookTrack) return;
  const card = bookTrack.querySelector('.book-card');
  const gap = Number.parseFloat(getComputedStyle(bookTrack).columnGap || getComputedStyle(bookTrack).gap || 14);
  const cardWidth = card ? card.getBoundingClientRect().width : 280;
  const scrollAmount = (cardWidth + gap) * direction;
  bookTrack.scrollBy({ left: scrollAmount, behavior: 'smooth' });
}

bookPrev?.addEventListener('click', () => scrollBooks(-1));
bookNext?.addEventListener('click', () => scrollBooks(1));

function updateCrisisVolumeDisplay(volume) {
  if (crisisVolumeValue) {
    crisisVolumeValue.textContent = `${Math.round(volume)}%`;
  }
}

function bindCrisisVolumeControl(player) {
  if (!crisisVolume) return;

  const startingVolume = Number.parseFloat(crisisVolume.value || '60');
  player.setVolume(startingVolume);
  updateCrisisVolumeDisplay(startingVolume);

  crisisVolume.addEventListener('input', (event) => {
    const value = Number.parseFloat(event.target.value || '0');
    player.unMute();
    player.setVolume(value);
    updateCrisisVolumeDisplay(value);
  });
}

function initCrisisPlayer() {
  const crisisIframe = document.getElementById('crisis-video-player');
  if (!crisisIframe || !window.YT || typeof window.YT.Player !== 'function') return;

  crisisPlayer = new window.YT.Player(crisisIframe, {
    events: {
      onReady: ({ target }) => {
        bindCrisisVolumeControl(target);
      },
    },
  });
}

window.onYouTubeIframeAPIReady = () => {
  initCrisisPlayer();
};

if (window.YT && typeof window.YT.Player === 'function') {
  initCrisisPlayer();
}

function updateBodyModalLock() {
  const hasOpenModal =
    charityModal?.classList.contains('is-open') ||
    bookModal?.classList.contains('is-open') ||
    adminBookModal?.classList.contains('is-open');
  document.body.classList.toggle('modal-open', Boolean(hasOpenModal));
}

function trackBookView(card) {
  const index = card?.dataset.bookIndex;
  if (index === undefined) return;

  fetch(`/books/${index}/view`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }).catch(() => {});
}

function trackBookScroll(card) {
  const index = card?.dataset.bookIndex;
  if (index === undefined || trackedScrollBooks.has(index)) return;

  trackedScrollBooks.add(index);

  fetch(`/books/${index}/scroll`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }).catch(() => {});
}

function populateBookModal(data) {
  if (!bookModal) return;

  if (bookModalTitle) {
    bookModalTitle.textContent = data.title || 'Book details';
  }

  if (bookModalAuthor) {
    bookModalAuthor.textContent = data.author || 'Featured read';
  }

  if (bookModalDescription) {
    bookModalDescription.textContent = data.description || 'Description coming soon.';
  }

  if (bookModalLink) {
    bookModalLink.href = data.link || '#';
  }

  if (bookModalCover) {
    if (data.cover) {
      bookModalCover.src = data.cover;
      bookModalCover.alt = `${data.title || 'Book'} cover`;
      bookModalCover.style.display = 'block';
      bookModalCoverWrapper?.classList.remove('is-empty');
      bookModalCoverFallback?.classList.add('hidden');
    } else {
      bookModalCover.removeAttribute('src');
      bookModalCover.alt = '';
      bookModalCover.style.display = 'none';
      bookModalCoverWrapper?.classList.add('is-empty');
      bookModalCoverFallback?.classList.remove('hidden');
    }
  }

  bookModal.classList.add('is-open');
  updateBodyModalLock();
}

function openBookModalFromCard(card, trigger) {
  if (!card) return;

  trackBookView(card);

  const data = {
    title: card.dataset.bookTitle || card.querySelector('h3')?.textContent || '',
    author: card.dataset.bookAuthor || '',
    description: card.dataset.bookDescription || card.querySelector('.book-description')?.textContent || '',
    cover: card.dataset.bookCover || card.querySelector('.book-cover img')?.src || '',
    link: card.dataset.bookLink || card.querySelector('.book-actions a')?.href || '',
  };

  activeBookTrigger = trigger || null;
  activeBookTrigger?.setAttribute('aria-expanded', 'true');

  populateBookModal(data);
}

function closeBookModal() {
  if (!bookModal) return;
  bookModal.classList.remove('is-open');
  activeBookTrigger?.setAttribute('aria-expanded', 'false');
  activeBookTrigger = null;
  updateBodyModalLock();
}

function initBookScrollTracking() {
  if (!bookCards.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          trackBookScroll(entry.target);
        }
      });
    },
    {
      root: bookTrack || null,
      threshold: 0.6,
    }
  );

  bookCards.forEach((card) => observer.observe(card));
}

bookTriggerButtons.forEach((button) => {
  button.addEventListener('click', () => {
    openBookModalFromCard(button.closest('.book-card'), button);
  });
});

initBookScrollTracking();

bookModalCloseButtons.forEach((button) => button.addEventListener('click', closeBookModal));

bookModal?.addEventListener('click', (event) => {
  if (event.target === bookModal) {
    closeBookModal();
  }
});

function populateAdminBookForm(trigger) {
  if (!adminBookForm || !trigger) return;
  adminBookForm.action = trigger.dataset.action || adminBookForm.action;
  const titleInput = adminBookForm.querySelector('input[name="title"]');
  const authorInput = adminBookForm.querySelector('input[name="author"]');
  const descriptionInput = adminBookForm.querySelector('textarea[name="description"]');
  const affiliateInput = adminBookForm.querySelector('input[name="affiliate_url"]');
  const coverInput = adminBookForm.querySelector('input[name="cover_url"]');

  if (titleInput) titleInput.value = trigger.dataset.title || '';
  if (authorInput) authorInput.value = trigger.dataset.author || '';
  if (descriptionInput) descriptionInput.value = trigger.dataset.description || '';
  if (affiliateInput) affiliateInput.value = trigger.dataset.affiliateUrl || '';
  if (coverInput) coverInput.value = trigger.dataset.coverUrl || '';
}

function openAdminBookModal(trigger) {
  if (!adminBookModal) return;
  activeAdminTrigger = trigger;
  populateAdminBookForm(trigger);
  adminBookModal.classList.add('is-open');
  updateBodyModalLock();
  adminBookForm?.querySelector('input[name="title"]')?.focus();
}

function closeAdminBookModal() {
  if (!adminBookModal) return;
  adminBookModal.classList.remove('is-open');
  activeAdminTrigger = null;
  updateBodyModalLock();
}

adminBookEditTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => openAdminBookModal(trigger));
});

adminBookCloseButtons.forEach((button) => button.addEventListener('click', closeAdminBookModal));

adminBookModal?.addEventListener('click', (event) => {
  if (event.target === adminBookModal) {
    closeAdminBookModal();
  }
});

function openModal() {
  if (!charityModal) return;
  charityModal.classList.add('is-open');
  updateBodyModalLock();
}

function closeModal() {
  if (!charityModal) return;
  charityModal.classList.remove('is-open');
  updateBodyModalLock();
}

showCharitiesBtn?.addEventListener('click', openModal);
modalClose?.addEventListener('click', closeModal);
charityModal?.addEventListener('click', (event) => {
  if (event.target === charityModal) {
    closeModal();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    if (charityModal?.classList.contains('is-open')) closeModal();
    if (bookModal?.classList.contains('is-open')) closeBookModal();
    if (adminBookModal?.classList.contains('is-open')) closeAdminBookModal();
  }
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
