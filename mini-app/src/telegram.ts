export function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? null;
}

export function bootstrapTelegram() {
  const tg = getTelegramWebApp();
  if (!tg) return null;
  tg.ready();
  tg.expand();
  return tg;
}
