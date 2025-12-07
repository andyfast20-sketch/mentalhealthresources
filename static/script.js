const tags = Array.from(document.querySelectorAll('.tag'));
const cards = Array.from(document.querySelectorAll('.resource-card'));
const resetBtn = document.getElementById('filter-reset');
const dropdownTriggers = Array.from(document.querySelectorAll('[data-dropdown-toggle]'));
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
const bookModalLinks = Array.from(document.querySelectorAll('[data-book-modal-link]'));
const bookTriggerButtons = Array.from(document.querySelectorAll('[data-book-trigger]'));
const bookCards = Array.from(document.querySelectorAll('.book-card[data-book-index]'));
const bookModalCloseButtons = Array.from(document.querySelectorAll('[data-book-modal-close]'));
const adminBookModal = document.querySelector('[data-admin-book-modal]');
const adminBookForm = document.querySelector('[data-admin-book-form]');
const adminBookCloseButtons = Array.from(document.querySelectorAll('[data-admin-book-modal-close]'));
const adminBookEditTriggers = Array.from(document.querySelectorAll('[data-admin-book-edit-trigger]'));
const adminCharityModal = document.querySelector('[data-admin-charity-modal]');
const adminCharityForm = document.querySelector('[data-admin-charity-form]');
const adminCharityTriggers = Array.from(document.querySelectorAll('[data-admin-charity-open]'));
const adminCharityCloseButtons = Array.from(document.querySelectorAll('[data-admin-charity-close]'));
const adminCharityTitle = document.querySelector('[data-admin-charity-modal-title]');
const adminCharitySubmit = document.querySelector('[data-admin-charity-submit]');
const mediaSelects = Array.from(document.querySelectorAll('[data-media-url-select]'));
const activityEditToggles = Array.from(document.querySelectorAll('[data-activity-edit-toggle]'));
const didYouKnowEditToggles = Array.from(document.querySelectorAll('[data-didyouknow-edit-toggle]'));
const mediaEditToggles = Array.from(document.querySelectorAll('[data-media-edit-toggle]'));
const charityModal = document.querySelector('[data-charity-modal]');
const charityModalTitle = document.querySelector('[data-charity-modal-title]');
const charityModalTelephones = Array.from(document.querySelectorAll('[data-charity-modal-telephone]'));
const charityModalTelephoneWrapper = document.querySelector('[data-charity-telephone-wrapper]');
const charityModalHoursLabel = document.querySelector('[data-charity-modal-hours-label]');
const charityModalHours = document.querySelector('[data-charity-modal-hours]');
const charityModalTextNumber = document.querySelector('[data-charity-modal-text-number]');
const charityModalEmail = document.querySelector('[data-charity-modal-email]');
const charityModalDescription = document.querySelector('[data-charity-modal-description]');
const charityFeatureList = document.querySelector('[data-charity-feature-list]');
const charityModalLink = document.querySelector('[data-charity-modal-link]');
const charityHelplineCard = document.querySelector('[data-charity-helpline-card]');
const charityTextCard = document.querySelector('[data-charity-text-card]');
const charityEmailCard = document.querySelector('[data-charity-email-card]');
const charityModalCloseButtons = Array.from(document.querySelectorAll('[data-charity-modal-close]'));
const charityTriggerButtons = Array.from(document.querySelectorAll('[data-charity-trigger]'));
const coffeeModal = document.querySelector('[data-coffee-modal]');
const crisisVolume = document.querySelector('[data-crisis-volume]');
const crisisVolumeValue = document.querySelector('[data-crisis-volume-value]');
const anxietyModal = document.querySelector('[data-anxiety-modal]');
const anxietyTriggers = Array.from(document.querySelectorAll('[data-anxiety-trigger]'));
const anxietyCloseButtons = Array.from(document.querySelectorAll('[data-anxiety-close]'));
const anxietyVideoModal = document.querySelector('[data-anxiety-video-modal]');
const anxietyVideoTriggers = Array.from(document.querySelectorAll('[data-anxiety-video-trigger]'));
const anxietyVideoCloseButtons = Array.from(document.querySelectorAll('[data-anxiety-video-close]'));
const anxietyVideoFrame = document.querySelector('[data-anxiety-video]');
const adminScrollContainer = document.querySelector('[data-admin-scroll-target]');
let crisisPlayer;
let activeBookTrigger = null;
let activeAdminTrigger = null;

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
    bookModal?.classList.contains('is-open') ||
    adminBookModal?.classList.contains('is-open') ||
    adminCharityModal?.classList.contains('is-open') ||
    charityModal?.classList.contains('is-open') ||
    anxietyModal?.classList.contains('is-open') ||
    anxietyVideoModal?.classList.contains('is-open') ||
    coffeeModal?.classList.contains('is-open');
  document.body.classList.toggle('modal-open', Boolean(hasOpenModal));
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

  if (bookModalLinks.length) {
    const resolvedLink = (data.link || '').trim();
    bookModalLinks.forEach((link) => {
      if (resolvedLink) {
        link.href = resolvedLink;
        link.removeAttribute('aria-disabled');
        link.classList.remove('is-disabled');
      } else {
        link.href = '#';
        link.setAttribute('aria-disabled', 'true');
        link.classList.add('is-disabled');
      }
      link.rel = 'noopener sponsored';
      link.target = '_blank';
    });
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

  recordBookView(card);

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

function recordBookView(card) {
  if (!card) return;
  const slug = card.dataset.bookSlug;
  if (!slug) return;

  fetch(`/books/${encodeURIComponent(slug)}/view`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  }).catch((error) => {
    console.warn('Could not record book view', error);
  });
}

function closeBookModal() {
  if (!bookModal) return;
  bookModal.classList.remove('is-open');
  activeBookTrigger?.setAttribute('aria-expanded', 'false');
  activeBookTrigger = null;
  updateBodyModalLock();
}

bookTriggerButtons.forEach((button) => {
  button.addEventListener('click', () => {
    openBookModalFromCard(button.closest('.book-card'), button);
  });
});

bookModalCloseButtons.forEach((button) => button.addEventListener('click', closeBookModal));

bookModalLinks.forEach((link) => {
  link.addEventListener('click', (event) => {
    const href = link.getAttribute('href');
    const isDisabled =
      link.classList.contains('is-disabled') || link.getAttribute('aria-disabled') === 'true' || !href || href === '#';

    if (isDisabled) {
      event.preventDefault();
      return;
    }

    event.preventDefault();

    const newTab = window.open(href, '_blank', 'noopener');

    if (newTab) {
      newTab.opener = null;
    } else {
      window.location.href = href;
    }

    closeBookModal();
  });
});

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
  const coverSelect = adminBookForm.querySelector('[data-media-url-select][data-target-input="cover_url"]');

  if (titleInput) titleInput.value = trigger.dataset.title || '';
  if (authorInput) authorInput.value = trigger.dataset.author || '';
  if (descriptionInput) descriptionInput.value = trigger.dataset.description || '';
  if (affiliateInput) affiliateInput.value = trigger.dataset.affiliateUrl || '';
  if (coverInput) coverInput.value = trigger.dataset.coverUrl || '';
  if (coverSelect) coverSelect.value = trigger.dataset.coverUrl || '';
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

function populateAdminCharityForm(trigger) {
  if (!adminCharityForm || !trigger) return;
  adminCharityForm.action = trigger.dataset.action || adminCharityForm.action;

  const nameInput = adminCharityForm.querySelector('input[name="name"]');
  const descriptionInput = adminCharityForm.querySelector('textarea[name="description"]');
  const logoInput = adminCharityForm.querySelector('input[name="logo_url"]');
  const logoSelect = adminCharityForm.querySelector('[data-media-url-select][data-target-input="logo_url"]');
  const websiteInput = adminCharityForm.querySelector('input[name="website_url"]');
  const telephoneInput = adminCharityForm.querySelector('input[name="telephone"]');
  const contactEmailInput = adminCharityForm.querySelector('input[name="contact_email"]');
  const textNumberInput = adminCharityForm.querySelector('input[name="text_number"]');
  const helplineHoursInput = adminCharityForm.querySelector('input[name="helpline_hours"]');
  const charityFeatureInputs = {
    has_helpline: adminCharityForm.querySelector('input[name="has_helpline"]'),
    has_volunteers: adminCharityForm.querySelector('input[name="has_volunteers"]'),
    has_crisis_info: adminCharityForm.querySelector('input[name="has_crisis_info"]'),
    has_text_support: adminCharityForm.querySelector('input[name="has_text_support"]'),
    has_email_support: adminCharityForm.querySelector('input[name="has_email_support"]'),
    has_live_chat: adminCharityForm.querySelector('input[name="has_live_chat"]'),
  };

  if (nameInput) nameInput.value = trigger.dataset.charityName || '';
  if (descriptionInput) descriptionInput.value = trigger.dataset.charityDescription || '';
  if (logoInput) logoInput.value = trigger.dataset.charityLogo || '';
  if (logoSelect) logoSelect.value = trigger.dataset.charityLogo || '';
  if (websiteInput) websiteInput.value = trigger.dataset.charityWebsite || '';
  if (telephoneInput) telephoneInput.value = trigger.dataset.charityTelephone || '';
  if (contactEmailInput) contactEmailInput.value = trigger.dataset.charityContactEmail || '';
  if (textNumberInput) textNumberInput.value = trigger.dataset.charityTextNumber || '';
  if (helplineHoursInput) helplineHoursInput.value = trigger.dataset.charityHelplineHours || '';

  Object.entries(charityFeatureInputs).forEach(([key, input]) => {
    if (!input) return;
    const datasetKey = key.replace(/_(\w)/g, (_, char) => char.toUpperCase());
    const rawValue = trigger.dataset[`charity${datasetKey.charAt(0).toUpperCase()}${datasetKey.slice(1)}`];
    input.checked = rawValue === 'True' || rawValue === 'true' || rawValue === '1';
    if (!trigger.dataset.charityName) {
      input.checked = false;
    }
  });

  if (adminCharityTitle && trigger.dataset.modalTitle) {
    adminCharityTitle.textContent = trigger.dataset.modalTitle;
  }

  if (adminCharitySubmit && trigger.dataset.submitLabel) {
    adminCharitySubmit.textContent = trigger.dataset.submitLabel;
  }
}

function openAdminCharityModal(trigger) {
  if (!adminCharityModal) return;
  populateAdminCharityForm(trigger);
  adminCharityModal.classList.add('is-open');
  updateBodyModalLock();
  adminCharityForm?.querySelector('input[name="name"]')?.focus();
}

function closeAdminCharityModal() {
  if (!adminCharityModal) return;
  adminCharityModal.classList.remove('is-open');
  updateBodyModalLock();
}

adminCharityTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => openAdminCharityModal(trigger));
});

adminCharityCloseButtons.forEach((button) => button.addEventListener('click', closeAdminCharityModal));

adminCharityModal?.addEventListener('click', (event) => {
  if (event.target === adminCharityModal) {
    closeAdminCharityModal();
  }
});

function toggleActivityEditForm(targetId) {
  if (!targetId) return;

  const form = document.querySelector(`[data-activity-form="${targetId}"]`);
  const toggles = Array.from(
    document.querySelectorAll(`[data-activity-edit-toggle][data-target="${targetId}"]`)
  );

  if (!form) return;

  const isHidden = form.classList.toggle('hidden');

  toggles.forEach((toggle) => {
    toggle.textContent = isHidden ? 'Edit' : 'Close edit';
    toggle.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
  });

  if (!isHidden) {
    form.querySelector('input, textarea')?.focus();
  }
}

activityEditToggles.forEach((toggle) => {
  toggle.addEventListener('click', () => toggleActivityEditForm(toggle.dataset.target));
});

function toggleDidYouKnowForm(targetId) {
  if (!targetId) return;

  const form = document.querySelector(`[data-didyouknow-form="${targetId}"]`);
  const toggles = Array.from(
    document.querySelectorAll(`[data-didyouknow-edit-toggle][data-target="${targetId}"]`)
  );

  if (!form) return;

  const isHidden = form.classList.toggle('hidden');

  toggles.forEach((toggle) => {
    toggle.textContent = isHidden ? 'Edit' : 'Close edit';
    toggle.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
  });

  if (!isHidden) {
    form.querySelector('input, textarea')?.focus();
  }
}

didYouKnowEditToggles.forEach((toggle) => {
  toggle.addEventListener('click', () => toggleDidYouKnowForm(toggle.dataset.target));
});

function toggleMediaEditForm(targetId) {
  if (!targetId) return;

  const form = document.querySelector(`[data-media-form="${targetId}"]`);
  const toggles = Array.from(
    document.querySelectorAll(`[data-media-edit-toggle][data-target="${targetId}"]`)
  );

  if (!form) return;

  const isHidden = form.classList.toggle('hidden');

  toggles.forEach((toggle) => {
    toggle.textContent = isHidden ? 'Edit' : 'Close edit';
    toggle.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
  });

  if (!isHidden) {
    form.querySelector('input, select, textarea')?.focus();
  }
}

mediaEditToggles.forEach((toggle) => {
  toggle.addEventListener('click', () => toggleMediaEditForm(toggle.dataset.target));
});

function bindMediaSelect(select) {
  if (!select) return;
  const targetName = select.dataset.targetInput;
  if (!targetName) return;

  select.addEventListener('change', () => {
    const form = select.closest('form');
    const targetInput = form?.querySelector(`input[name="${targetName}"]`);
    if (!targetInput) return;
    if (select.value) {
      try {
        const resolvedUrl = new URL(select.value, window.location.origin);
        targetInput.value = resolvedUrl.href;
      } catch (error) {
        targetInput.value = select.value;
      }
    }
  });
}

mediaSelects.forEach(bindMediaSelect);

const charityFeatureConfig = [
  { key: 'charityHasHelpline', label: 'Helpline' },
  { key: 'charityHasVolunteers', label: 'Volunteers' },
  { key: 'charityHasCrisisInfo', label: 'Crisis info' },
  { key: 'charityHasTextSupport', label: 'Text support' },
  { key: 'charityHasEmailSupport', label: 'Email support' },
  { key: 'charityHasLiveChat', label: 'Live chat' },
];

function parseDatasetBoolean(value) {
  return value === 'True' || value === 'true' || value === '1';
}

function renderCharityFeatures(trigger) {
  if (!charityFeatureList) return;
  charityFeatureList.innerHTML = '';

  charityFeatureConfig
    .filter(({ key }) => parseDatasetBoolean(trigger.dataset[key]))
    .forEach(({ label }) => {
      const feature = document.createElement('div');
      feature.className = 'charity-feature';
      feature.innerHTML = `<span class="feature-icon" aria-hidden="true">✓</span><span>${label}</span>`;
      charityFeatureList.appendChild(feature);
    });
}

function openCharityModal(trigger) {
  if (!charityModal || !trigger) return;

  if (charityModalTitle) charityModalTitle.textContent = trigger.dataset.charityName || 'Charity';
  if (charityModalDescription)
    charityModalDescription.textContent = trigger.dataset.charityDescription || 'Learn more about this organisation.';

  const telephone = (trigger.dataset.charityTelephone || '').trim();
  const textNumber = (trigger.dataset.charityTextNumber || '').trim();
  const contactEmail = (trigger.dataset.charityContactEmail || '').trim();
  const helplineHours = (trigger.dataset.charityHelplineHours || '').trim();

  if (charityModalTelephoneWrapper) {
    charityModalTelephoneWrapper.hidden = !telephone;
  }
  if (charityModalHoursLabel) {
    charityModalHoursLabel.textContent = helplineHours ? `Open: ${helplineHours}` : '';
  }

  charityModalTelephones.forEach((element) => {
    element.textContent = telephone;
  });

  if (charityHelplineCard) {
    charityHelplineCard.hidden = !telephone;
  }
  if (charityModalHours) {
    charityModalHours.textContent = helplineHours || 'Check their site for the latest opening times.';
  }

  if (charityTextCard) {
    charityTextCard.hidden = !textNumber;
  }
  if (charityModalTextNumber) {
    charityModalTextNumber.textContent = textNumber;
  }

  if (charityEmailCard) {
    charityEmailCard.hidden = !contactEmail;
  }
  if (charityModalEmail) {
    charityModalEmail.textContent = contactEmail;
  }

  if (charityModalLink) {
    charityModalLink.href = trigger.dataset.charityWebsite || '#';
  }

  renderCharityFeatures(trigger);

  charityModal.classList.add('is-open');
  updateBodyModalLock();
}

function closeCharityModal() {
  if (!charityModal) return;
  charityModal.classList.remove('is-open');
  updateBodyModalLock();
}

charityTriggerButtons.forEach((trigger) => {
  trigger.addEventListener('click', () => openCharityModal(trigger));
});

charityModalCloseButtons.forEach((button) => button.addEventListener('click', closeCharityModal));

charityModal?.addEventListener('click', (event) => {
  if (event.target === charityModal) {
    closeCharityModal();
  }
});

function openAnxietyModal() {
  if (!anxietyModal) return;
  anxietyModal.classList.add('is-open');
  updateBodyModalLock();
}

function closeAnxietyModal() {
  if (!anxietyModal) return;
  anxietyModal.classList.remove('is-open');
  updateBodyModalLock();
}

anxietyTriggers.forEach((trigger) => trigger.addEventListener('click', openAnxietyModal));
anxietyCloseButtons.forEach((button) => button.addEventListener('click', closeAnxietyModal));

anxietyModal?.addEventListener('click', (event) => {
  if (event.target === anxietyModal) {
    closeAnxietyModal();
  }
});

function playAnxietyVideo() {
  if (!anxietyVideoFrame) return;
  const baseSrc = anxietyVideoFrame.dataset.videoSrc || '';
  anxietyVideoFrame.src = baseSrc ? `${baseSrc}&autoplay=1` : '';
}

function stopAnxietyVideo() {
  if (!anxietyVideoFrame) return;
  anxietyVideoFrame.src = anxietyVideoFrame.dataset.videoSrc || '';
}

function openAnxietyVideoModal() {
  if (!anxietyVideoModal) return;
  playAnxietyVideo();
  anxietyVideoModal.classList.add('is-open');
  updateBodyModalLock();
}

function closeAnxietyVideoModal() {
  if (!anxietyVideoModal) return;
  stopAnxietyVideo();
  anxietyVideoModal.classList.remove('is-open');
  updateBodyModalLock();
}

anxietyVideoTriggers.forEach((trigger) => trigger.addEventListener('click', openAnxietyVideoModal));
anxietyVideoCloseButtons.forEach((button) => button.addEventListener('click', closeAnxietyVideoModal));

anxietyVideoModal?.addEventListener('click', (event) => {
  if (event.target === anxietyVideoModal) {
    closeAnxietyVideoModal();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    if (bookModal?.classList.contains('is-open')) closeBookModal();
    if (adminBookModal?.classList.contains('is-open')) closeAdminBookModal();
    if (adminCharityModal?.classList.contains('is-open')) closeAdminCharityModal();
    if (anxietyModal?.classList.contains('is-open')) closeAnxietyModal();
    if (anxietyVideoModal?.classList.contains('is-open')) closeAnxietyVideoModal();
  }
});

function focusAdminSection(sectionId) {
  if (!sectionId) return;

  const target = document.getElementById(sectionId);
  if (!target) return;

  target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  target.classList.add('admin-section-highlight');

  const focusable = target.querySelector('input, textarea, button');
  focusable?.focus({ preventScroll: true });

  window.setTimeout(() => target.classList.remove('admin-section-highlight'), 1500);
}

if (adminScrollContainer?.dataset.adminScrollTarget) {
  const targetSection = adminScrollContainer.dataset.adminScrollTarget;
  window.requestAnimationFrame(() => focusAdminSection(targetSection));
}

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

// Swap in a friendly fallback if a charity logo is missing or fails to load
const charityLogoWrappers = Array.from(document.querySelectorAll('.charity-logo'));

function showCharityLogoFallback(wrapper, image) {
  if (image) {
    image.classList.add('hidden');
    image.removeAttribute('src');
  }

  const fallback = wrapper?.querySelector('.logo-fallback');
  fallback?.classList.remove('hidden');
}

charityLogoWrappers.forEach((wrapper) => {
  const image = wrapper.querySelector('img');
  if (!image) return;

  if (!image.getAttribute('src')) {
    showCharityLogoFallback(wrapper, image);
    return;
  }

  image.addEventListener('error', () => showCharityLogoFallback(wrapper, image));
});
