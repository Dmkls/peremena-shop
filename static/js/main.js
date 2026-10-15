// Подтверждение опасных действий: <form data-confirm="Удалить товар?">
document.addEventListener('submit', (e) => {
  const msg = e.target.dataset.confirm;
  if (msg && !window.confirm(msg)) e.preventDefault();
});

// Чек-лист правил пароля при регистрации: выполненное правило становится зелёной галочкой.
const PASSWORD_RULES = {
  'length': (v) => v.length >= 8,
  'not-numeric': (v) => v !== '' && !/^\d+$/.test(v),
};
document.addEventListener('input', (e) => {
  if (!e.target.matches('[data-password-rules]')) return;
  e.target.closest('.field').querySelectorAll('.pw-rules [data-rule]').forEach((li) => {
    li.classList.toggle('ok', PASSWORD_RULES[li.dataset.rule](e.target.value));
  });
});

// «В корзину» без перезагрузки: <form data-cart-add>. Без JS форма работает как обычная.
function toast(text, isError) {
  const el = document.createElement('div');
  el.className = 'toast' + (isError ? ' toast-error' : '');
  el.setAttribute('role', 'status');
  el.textContent = text;
  document.body.append(el);
  setTimeout(() => el.remove(), 2500);
}

document.addEventListener('submit', async (e) => {
  const form = e.target;
  if (!form.matches('[data-cart-add]')) return;
  e.preventDefault();
  const button = form.querySelector('button');
  button.disabled = true;
  try {
    const res = await fetch(form.action, {
      method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!res.headers.get('content-type')?.includes('application/json')) throw new Error('not json');
    const data = await res.json();
    document.querySelectorAll('[data-cart-count]').forEach((b) => { b.textContent = data.cart_count; });
    // data-cart-add="quiet" (страница товара): об успехе молчим, хватает счётчика; ошибку показываем всегда.
    if (!data.ok || form.dataset.cartAdd !== 'quiet') toast(data.message, !data.ok);
  } catch {
    form.submit();  // например, сессия истекла — пусть сервер разберётся обычным способом
  } finally {
    button.disabled = false;
  }
});

// Поле количества в корзине: при изменении сразу отправляем форму.
document.addEventListener('change', (e) => {
  if (e.target.matches('[data-autosubmit]')) e.target.form.requestSubmit();
});
