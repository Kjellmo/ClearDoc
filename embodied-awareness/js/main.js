window.addEventListener('scroll', () => {
  document.getElementById('nav').classList.toggle('scrolled', window.scrollY > 20);
});

function toggleMenu() {
  document.getElementById('navLinks').classList.toggle('open');
}

document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    document.getElementById('navLinks').classList.remove('open');
  });
});

let lang = 'no';

function toggleLang() {
  lang = lang === 'no' ? 'en' : 'no';
  document.querySelector('.lang-btn').textContent = lang === 'no' ? 'EN' : 'NO';
  applyLang();
}

function applyLang() {
  const showAttr = `data-${lang}`;
  const hideAttr = lang === 'no' ? 'data-en' : 'data-no';
  document.querySelectorAll(`[${showAttr}]`).forEach(el => { el.style.display = ''; });
  document.querySelectorAll(`[${hideAttr}]`).forEach(el => {
    if (!el.hasAttribute(showAttr)) el.style.display = 'none';
  });
  document.querySelectorAll('[data-placeholder-no], [data-placeholder-en]').forEach(el => {
    const ph = el.getAttribute(`data-placeholder-${lang}`);
    if (ph) el.placeholder = ph;
  });
  document.documentElement.lang = lang;
}

function handleNewsletter(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button');
  btn.textContent = lang === 'no' ? 'Takk!' : 'Thank you!';
  btn.disabled = true;
  setTimeout(() => {
    btn.textContent = lang === 'no' ? 'Meld meg på' : 'Subscribe';
    btn.disabled = false;
    e.target.reset();
  }, 3000);
}

function handleContact(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]:not([style*="none"])');
  const original = btn.textContent;
  btn.textContent = lang === 'no' ? 'Sender…' : 'Sending…';
  btn.disabled = true;
  setTimeout(() => {
    btn.textContent = lang === 'no' ? 'Melding sendt!' : 'Message sent!';
    setTimeout(() => { btn.textContent = original; btn.disabled = false; e.target.reset(); }, 2500);
  }, 1000);
}

const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.opacity = '1';
      e.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.08 });

document.querySelectorAll('.card, .event-card, .testimonial, .faq-item').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(24px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(el);
});
