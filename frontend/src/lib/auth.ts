export async function login(email: string, password: string): Promise<void> {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Falha no login.');
  }
}

export async function logout(): Promise<void> {
  await fetch('/api/logout', { method: 'POST' });
}

export async function checkSession(): Promise<boolean> {
  const res = await fetch('/api/me');
  if (!res.ok) return false;
  const data = await res.json();
  return !!data.authenticated;
}
