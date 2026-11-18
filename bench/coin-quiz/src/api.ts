// All calls go to the game server with the signed-in user's session.
const BASE = 'https://api.coinquiz.example';

export const api = {
  async post(path: string, body?: unknown) {
    const res = await fetch(BASE + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body ?? {}) });
    return res.json();
  },
};
