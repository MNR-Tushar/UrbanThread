import { useState, useEffect, useContext, createContext, useCallback } from "react";

const API = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) || "http://127.0.0.1:8000";

// ─── Auth Context ─────────────────────────────────────────────────────────────
const AuthContext = createContext(null);
function useAuth() { return useContext(AuthContext); }

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ut_user") || "null"); } catch { return null; }
  });
  const [tokens, setTokens] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ut_tokens") || "null"); } catch { return null; }
  });

  const login = (userData, tokenData) => {
    setUser(userData);
    setTokens(tokenData);
    localStorage.setItem("ut_user", JSON.stringify(userData));
    localStorage.setItem("ut_tokens", JSON.stringify(tokenData));
  };

  const updateUser = (partial) => {
    setUser(prev => {
      const next = { ...(prev || {}), ...(partial || {}) };
      localStorage.setItem("ut_user", JSON.stringify(next));
      return next;
    });
  };

  const logout = () => {
    setUser(null);
    setTokens(null);
    localStorage.removeItem("ut_user");
    localStorage.removeItem("ut_tokens");
  };

  const authFetch = useCallback(async (url, opts = {}) => {
    const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
    if (tokens?.access) headers["Authorization"] = `Bearer ${tokens.access}`;
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401) { logout(); throw new Error("Unauthorized"); }
    return res;
  }, [tokens]);

  return (
    <AuthContext.Provider value={{ user, tokens, login, logout, updateUser, authFetch, isAdmin: user?.is_staff }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Cart Context ─────────────────────────────────────────────────────────────
const CartContext = createContext(null);
function useCart() { return useContext(CartContext); }

function CartProvider({ children }) {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const { authFetch, user } = useAuth();

  const fetchCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await authFetch(`${API}/cart/my_cart/`);
      if (res.ok) setCart(await res.json());
    } catch {}
    setLoading(false);
  }, [authFetch, user]);

  useEffect(() => { fetchCart(); }, [fetchCart]);

  const addItem = async (product_id, color_id, size_id, quantity = 1) => {
    const res = await authFetch(`${API}/cart/add_item/`, {
      method: "POST", body: JSON.stringify({ product_id, color_id, size_id, quantity })
    });
    if (res.ok) await fetchCart();
    return res;
  };

  const removeItem = async (item_id) => {
    await authFetch(`${API}/cart/remove_item/`, { method: "DELETE", body: JSON.stringify({ item_id }) });
    await fetchCart();
  };

  const updateItem = async (item_id, quantity) => {
    const res = await authFetch(`${API}/cart/update_item/`, {
      method: "PATCH", body: JSON.stringify({ item_id, quantity })
    });
    if (res.ok) await fetchCart();
    return res;
  };

  const clearCart = async () => {
    await authFetch(`${API}/cart/clear_cart/`, { method: "DELETE" });
    await fetchCart();
  };

  return (
    <CartContext.Provider value={{ cart, loading, fetchCart, addItem, removeItem, updateItem, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --ink: #0f0e0c;
    --ink2: #2c2a26;
    --ink3: #5a5750;
    --sand: #f7f4ef;
    --sand2: #ede9e0;
    --sand3: #ddd8cb;
    --gold: #b89a5a;
    --gold2: #8c7040;
    --cream: #faf8f4;
    --white: #ffffff;
    --danger: #c0392b;
    --success: #1a6b45;
    --r: 2px;
    --r2: 6px;
    --r3: 12px;
    --shadow: 0 1px 4px rgba(0,0,0,0.08);
    --shadow2: 0 4px 20px rgba(0,0,0,0.12);
    --transition: 0.2s cubic-bezier(0.4,0,0.2,1);
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--cream);
    color: var(--ink);
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  h1, h2, h3, h4 {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 400;
    line-height: 1.15;
  }

  /* ── Layout ── */
  .container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }
  .page { min-height: calc(100vh - 64px); }

  /* ── Navbar ── */
  .navbar {
    position: sticky; top: 0; z-index: 100;
    background: var(--white);
    border-bottom: 1px solid var(--sand3);
    height: 64px;
    display: flex; align-items: center;
  }
  .navbar-inner {
    width: 100%; max-width: 1280px; margin: 0 auto; padding: 0 24px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .navbar-logo {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px; font-weight: 500; letter-spacing: 0.08em;
    color: var(--ink); cursor: pointer;
    text-transform: uppercase;
  }
  .navbar-logo span { color: var(--gold); }
  .navbar-links { display: flex; align-items: center; gap: 28px; }
  .nav-link {
    font-size: 13px; font-weight: 400; letter-spacing: 0.06em;
    color: var(--ink2); cursor: pointer; text-transform: uppercase;
    padding: 4px 0; position: relative; border: none; background: none;
    transition: color var(--transition);
  }
  .nav-link:hover { color: var(--gold); }
  .nav-link.active {
    color: var(--ink);
    border-bottom: 1px solid var(--ink);
  }
  .navbar-actions { display: flex; align-items: center; gap: 12px; }
  .icon-btn {
    width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
    background: none; border: 1px solid transparent; border-radius: var(--r2);
    cursor: pointer; color: var(--ink2); font-size: 18px; position: relative;
    transition: all var(--transition);
  }
  .icon-btn:hover { background: var(--sand); border-color: var(--sand3); }
  .cart-badge {
    position: absolute; top: 4px; right: 4px;
    width: 16px; height: 16px; border-radius: 50%;
    background: var(--ink); color: var(--white);
    font-size: 10px; font-weight: 500; display: flex; align-items: center; justify-content: center;
    font-family: 'DM Sans', sans-serif;
  }

  /* ── Buttons ── */
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 0 24px; height: 44px; border-radius: var(--r2);
    font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500;
    letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer;
    border: 1px solid transparent; transition: all var(--transition);
  }
  .btn-primary {
    background: var(--ink); color: var(--white); border-color: var(--ink);
  }
  .btn-primary:hover { background: var(--ink2); }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-outline {
    background: transparent; color: var(--ink); border-color: var(--ink);
  }
  .btn-outline:hover { background: var(--ink); color: var(--white); }
  .btn-ghost {
    background: transparent; color: var(--ink2); border-color: transparent;
  }
  .btn-ghost:hover { background: var(--sand); }
  .btn-gold {
    background: var(--gold); color: var(--white); border-color: var(--gold);
  }
  .btn-gold:hover { background: var(--gold2); }
  .btn-sm { height: 34px; padding: 0 16px; font-size: 12px; }
  .btn-lg { height: 52px; padding: 0 36px; font-size: 14px; }
  .btn-full { width: 100%; }
  .btn-danger { background: var(--danger); color: var(--white); border-color: var(--danger); }

  /* ── Forms ── */
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-label { font-size: 12px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink3); }
  .form-input {
    width: 100%; height: 44px; padding: 0 14px;
    border: 1px solid var(--sand3); border-radius: var(--r2);
    font-family: 'DM Sans', sans-serif; font-size: 14px; color: var(--ink);
    background: var(--white); outline: none;
    transition: border-color var(--transition);
  }
  .form-input:focus { border-color: var(--ink); }
  .form-input::placeholder { color: var(--ink3); }
  .form-select {
    width: 100%; height: 44px; padding: 0 14px;
    border: 1px solid var(--sand3); border-radius: var(--r2);
    font-family: 'DM Sans', sans-serif; font-size: 14px; color: var(--ink);
    background: var(--white); outline: none; cursor: pointer;
    transition: border-color var(--transition); appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235a5750' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 14px center;
  }
  .form-select:focus { border-color: var(--ink); }
  .form-textarea {
    width: 100%; padding: 12px 14px; min-height: 100px;
    border: 1px solid var(--sand3); border-radius: var(--r2);
    font-family: 'DM Sans', sans-serif; font-size: 14px; color: var(--ink);
    background: var(--white); outline: none; resize: vertical;
    transition: border-color var(--transition);
  }
  .form-textarea:focus { border-color: var(--ink); }
  .form-error { font-size: 12px; color: var(--danger); }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .form-stack { display: flex; flex-direction: column; gap: 18px; }

  /* ── Cards ── */
  .card {
    background: var(--white); border: 1px solid var(--sand3);
    border-radius: var(--r3); overflow: hidden;
  }
  .card-body { padding: 24px; }

  /* ── Product Card ── */
  .product-card {
    background: var(--white); border: 1px solid var(--sand3);
    border-radius: var(--r2); overflow: hidden; cursor: pointer;
    transition: all var(--transition);
  }
  .product-card:hover { border-color: var(--gold); box-shadow: var(--shadow2); transform: translateY(-2px); }
  .product-img {
    width: 100%; aspect-ratio: 3/4; object-fit: cover;
    background: var(--sand);
    display: flex; align-items: center; justify-content: center;
    color: var(--ink3); font-size: 13px; letter-spacing: 0.04em;
  }
  .product-img img { width: 100%; height: 100%; object-fit: cover; }
  .product-info { padding: 14px 16px; }
  .product-category { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink3); margin-bottom: 4px; }
  .product-name { font-family: 'Cormorant Garamond', serif; font-size: 18px; margin-bottom: 6px; }
  .product-price { font-size: 14px; font-weight: 500; color: var(--ink2); }
  .product-price .original { text-decoration: line-through; color: var(--ink3); margin-right: 8px; font-weight: 400; }
  .product-price .discount { color: var(--gold2); }

  /* ── Badge ── */
  .badge {
    display: inline-flex; align-items: center;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 500; letter-spacing: 0.04em;
  }
  .badge-success { background: #d4edda; color: #1a6b45; }
  .badge-danger { background: #fde8e8; color: var(--danger); }
  .badge-warning { background: #fef3cd; color: #8c6500; }
  .badge-neutral { background: var(--sand2); color: var(--ink2); }
  .badge-gold { background: #f5ecda; color: var(--gold2); }

  /* ── Grid Layouts ── */
  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
  }
  .section { padding: 60px 0; }
  .section-sm { padding: 32px 0; }

  /* ── Hero ── */
  .hero {
    background: var(--ink);
    min-height: 520px;
    display: flex; align-items: center;
    position: relative; overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute; inset: 0;
    background: repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(255,255,255,0.015) 40px, rgba(255,255,255,0.015) 80px);
  }
  .hero-content { position: relative; z-index: 1; color: var(--white); max-width: 560px; }
  .hero-eyebrow { font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); margin-bottom: 20px; }
  .hero-title { font-family: 'Cormorant Garamond', serif; font-size: clamp(48px, 6vw, 80px); font-weight: 300; line-height: 1.05; margin-bottom: 24px; }
  .hero-sub { font-size: 15px; color: rgba(255,255,255,0.65); line-height: 1.7; margin-bottom: 36px; max-width: 420px; }

  /* ── Page Header ── */
  .page-header { padding: 48px 0 32px; border-bottom: 1px solid var(--sand3); margin-bottom: 40px; }
  .page-title { font-size: clamp(32px, 4vw, 52px); font-weight: 300; }
  .page-subtitle { font-size: 14px; color: var(--ink3); margin-top: 8px; }

  /* ── Filters ── */
  .filters-bar {
    display: flex; align-items: center; gap: 12px;
    padding: 16px 0; border-bottom: 1px solid var(--sand3);
    margin-bottom: 32px; flex-wrap: wrap;
  }
  .filter-chip {
    padding: 6px 16px; border-radius: 20px;
    border: 1px solid var(--sand3); background: var(--white);
    font-size: 12px; letter-spacing: 0.04em; cursor: pointer;
    transition: all var(--transition); color: var(--ink2);
  }
  .filter-chip:hover { border-color: var(--ink); }
  .filter-chip.active { background: var(--ink); color: var(--white); border-color: var(--ink); }

  /* ── Product Detail ── */
  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; padding: 60px 0; }
  .detail-images { position: sticky; top: 80px; }
  .main-image {
    width: 100%; aspect-ratio: 3/4; object-fit: cover;
    background: var(--sand); border-radius: var(--r2);
    display: flex; align-items: center; justify-content: center;
    color: var(--ink3); font-size: 13px; overflow: hidden;
  }
  .main-image img { width: 100%; height: 100%; object-fit: cover; }
  .thumb-list { display: flex; gap: 8px; margin-top: 12px; }
  .thumb {
    width: 72px; height: 90px; border-radius: var(--r);
    background: var(--sand); border: 2px solid transparent;
    cursor: pointer; overflow: hidden; flex-shrink: 0;
    transition: border-color var(--transition);
  }
  .thumb.active { border-color: var(--ink); }
  .thumb img { width: 100%; height: 100%; object-fit: cover; }
  .detail-info { display: flex; flex-direction: column; gap: 24px; }
  .detail-brand { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink3); }
  .detail-name { font-size: clamp(28px, 3vw, 42px); font-weight: 300; }
  .detail-price { display: flex; align-items: baseline; gap: 12px; }
  .detail-price .main-price { font-family: 'Cormorant Garamond', serif; font-size: 30px; }
  .detail-price .old-price { font-size: 18px; text-decoration: line-through; color: var(--ink3); }
  .detail-price .save-badge { font-size: 12px; }
  .size-grid { display: flex; gap: 8px; flex-wrap: wrap; }
  .size-btn {
    min-width: 52px; height: 40px; padding: 0 12px;
    border: 1px solid var(--sand3); border-radius: var(--r);
    font-size: 13px; cursor: pointer; transition: all var(--transition);
    background: var(--white); color: var(--ink);
  }
  .size-btn:hover { border-color: var(--ink); }
  .size-btn.selected { background: var(--ink); color: var(--white); border-color: var(--ink); }
  .color-grid { display: flex; gap: 10px; flex-wrap: wrap; }
  .color-btn {
    width: 32px; height: 32px; border-radius: 50%;
    border: 3px solid transparent; cursor: pointer;
    transition: all var(--transition); outline: none;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.15);
  }
  .color-btn.selected { border-color: var(--ink); }
  .qty-control { display: flex; align-items: center; gap: 0; border: 1px solid var(--sand3); border-radius: var(--r2); width: fit-content; }
  .qty-btn {
    width: 40px; height: 44px; background: none; border: none;
    font-size: 18px; cursor: pointer; color: var(--ink2);
    transition: background var(--transition);
  }
  .qty-btn:hover { background: var(--sand); }
  .qty-val { width: 48px; text-align: center; font-size: 15px; font-weight: 500; }
  .divider { height: 1px; background: var(--sand3); }
  .spec-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--sand2); font-size: 13px; }
  .spec-label { color: var(--ink3); }

  /* ── Cart ── */
  .cart-layout { display: grid; grid-template-columns: 1fr 360px; gap: 48px; padding: 48px 0; }
  .cart-item-row {
    display: grid; grid-template-columns: 80px 1fr auto;
    gap: 16px; padding: 20px 0; border-bottom: 1px solid var(--sand3);
    align-items: start;
  }
  .cart-item-img {
    width: 80px; height: 100px; border-radius: var(--r);
    background: var(--sand); object-fit: cover; overflow: hidden;
  }
  .cart-item-img img { width: 100%; height: 100%; object-fit: cover; }
  .cart-item-name { font-family: 'Cormorant Garamond', serif; font-size: 18px; margin-bottom: 4px; }
  .cart-item-meta { font-size: 12px; color: var(--ink3); letter-spacing: 0.04em; }
  .cart-summary { background: var(--white); border: 1px solid var(--sand3); border-radius: var(--r3); padding: 28px; position: sticky; top: 80px; }
  .summary-row { display: flex; justify-content: space-between; font-size: 14px; padding: 8px 0; color: var(--ink2); }
  .summary-total { display: flex; justify-content: space-between; font-size: 18px; padding: 16px 0 0; border-top: 1px solid var(--sand3); margin-top: 8px; }
  .summary-title { font-family: 'Cormorant Garamond', serif; font-size: 22px; margin-bottom: 20px; }
  .coupon-row { display: flex; gap: 8px; margin: 16px 0; }
  .coupon-row .form-input { flex: 1; height: 40px; }

  /* ── Auth ── */
  .auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--sand); }
  .auth-card { background: var(--white); border-radius: var(--r3); border: 1px solid var(--sand3); padding: 48px; width: 100%; max-width: 420px; }
  .auth-logo { text-align: center; margin-bottom: 32px; }
  .auth-logo h1 { font-family: 'Cormorant Garamond', serif; font-size: 28px; letter-spacing: 0.08em; text-transform: uppercase; }
  .auth-logo span { color: var(--gold); }
  .auth-switch { text-align: center; font-size: 13px; color: var(--ink3); margin-top: 20px; }
  .auth-switch button { background: none; border: none; color: var(--ink); font-weight: 500; cursor: pointer; text-decoration: underline; }

  /* ── Orders ── */
  .order-card {
    background: var(--white); border: 1px solid var(--sand3);
    border-radius: var(--r2); padding: 24px; margin-bottom: 16px;
  }
  .order-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
  .order-number { font-family: 'Cormorant Garamond', serif; font-size: 20px; }
  .order-date { font-size: 12px; color: var(--ink3); }
  .order-items-list { border-top: 1px solid var(--sand2); padding-top: 16px; display: flex; flex-direction: column; gap: 12px; }
  .order-item { display: flex; gap: 12px; align-items: center; }
  .order-item-img { width: 50px; height: 62px; background: var(--sand); border-radius: var(--r); flex-shrink: 0; overflow: hidden; }
  .order-item-img img { width: 100%; height: 100%; object-fit: cover; }
  .order-footer { border-top: 1px solid var(--sand2); margin-top: 16px; padding-top: 16px; display: flex; justify-content: space-between; align-items: center; }

  /* ── Profile ── */
  .profile-layout { display: grid; grid-template-columns: 240px 1fr; gap: 40px; padding: 48px 0; }
  .profile-nav { background: var(--white); border: 1px solid var(--sand3); border-radius: var(--r2); padding: 8px; height: fit-content; position: sticky; top: 80px; }
  .profile-nav-link {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 16px; border-radius: var(--r); cursor: pointer;
    font-size: 14px; color: var(--ink2); transition: all var(--transition);
    border: none; background: none; width: 100%; text-align: left;
  }
  .profile-nav-link:hover { background: var(--sand); }
  .profile-nav-link.active { background: var(--sand2); color: var(--ink); font-weight: 500; }
  .profile-section-title { font-family: 'Cormorant Garamond', serif; font-size: 28px; margin-bottom: 24px; }

  /* ── Checkout ── */
  .checkout-layout { display: grid; grid-template-columns: 1fr 380px; gap: 48px; padding: 48px 0; }

  /* ── Empty State ── */
  .empty-state { text-align: center; padding: 80px 24px; }
  .empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.3; }
  .empty-title { font-family: 'Cormorant Garamond', serif; font-size: 28px; margin-bottom: 8px; }
  .empty-sub { color: var(--ink3); font-size: 14px; }

  /* ── Toast ── */
  .toast-container { position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
  .toast {
    background: var(--ink); color: var(--white); padding: 14px 20px;
    border-radius: var(--r2); font-size: 14px; max-width: 320px;
    display: flex; align-items: center; gap: 10px;
    box-shadow: var(--shadow2);
    animation: slideUp 0.3s ease;
  }
  .toast.success { background: var(--success); }
  .toast.error { background: var(--danger); }
  @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

  /* ── Spinner ── */
  .spinner {
    width: 24px; height: 24px;
    border: 2px solid var(--sand3);
    border-top-color: var(--ink);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  .spinner-sm { width: 16px; height: 16px; border-width: 2px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-screen { display: flex; align-items: center; justify-content: center; padding: 80px; }

  /* ── Misc ── */
  .text-gold { color: var(--gold); }
  .text-muted { color: var(--ink3); }
  .text-sm { font-size: 13px; }
  .text-xs { font-size: 11px; }
  .flex { display: flex; }
  .flex-center { display: flex; align-items: center; justify-content: center; }
  .gap-8 { gap: 8px; }
  .gap-12 { gap: 12px; }
  .gap-16 { gap: 16px; }
  .mt-4 { margin-top: 4px; }
  .mt-8 { margin-top: 8px; }
  .mt-16 { margin-top: 16px; }
  .mt-24 { margin-top: 24px; }
  .fw-500 { font-weight: 500; }
  .section-label { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink3); margin-bottom: 8px; }
  .star { color: var(--gold); font-size: 14px; }
  .review-card { background: var(--sand); border-radius: var(--r2); padding: 16px; margin-bottom: 12px; }
  .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .no-select { user-select: none; }
  .pagination { display: flex; gap: 8px; align-items: center; margin-top: 40px; justify-content: center; }
  .page-btn { width: 36px; height: 36px; border: 1px solid var(--sand3); border-radius: var(--r); background: var(--white); cursor: pointer; font-size: 13px; transition: all var(--transition); display: flex; align-items: center; justify-content: center; }
  .page-btn:hover { border-color: var(--ink); }
  .page-btn.active { background: var(--ink); color: var(--white); border-color: var(--ink); }
  .inventory-badge { font-size: 11px; font-weight: 500; }
  .tag { display: inline-flex; padding: 2px 8px; background: var(--sand2); border-radius: 20px; font-size: 11px; letter-spacing: 0.04em; color: var(--ink2); }
  .address-card { border: 1px solid var(--sand3); border-radius: var(--r2); padding: 16px; background: var(--white); margin-bottom: 12px; }
  .address-card.selected { border-color: var(--ink); border-width: 2px; }

  @media (max-width: 900px) {
    .detail-grid { grid-template-columns: 1fr; gap: 32px; }
    .cart-layout { grid-template-columns: 1fr; }
    .checkout-layout { grid-template-columns: 1fr; }
    .profile-layout { grid-template-columns: 1fr; }
    .form-row { grid-template-columns: 1fr; }
    .products-grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
    .navbar-links { display: none; }
  }
`;

// ─── Toast System ─────────────────────────────────────────────────────────────
const ToastContext = createContext(null);
function useToast() { return useContext(ToastContext); }

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const add = (msg, type = "default") => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
  };
  return (
    <ToastContext.Provider value={add}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast ${t.type}`}>
            <span>{t.type === "success" ? "✓" : t.type === "error" ? "✕" : "•"}</span>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ─── Stars ────────────────────────────────────────────────────────────────────
function Stars({ rating }) {
  return (
    <span>
      {[1,2,3,4,5].map(i => (
        <span key={i} className="star">{i <= rating ? "★" : "☆"}</span>
      ))}
    </span>
  );
}

// ─── Navbar ───────────────────────────────────────────────────────────────────
function Navbar({ page, setPage }) {
  const { user, logout } = useAuth();
  const { cart } = useCart();
  const cartCount = cart?.total_items || 0;

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-logo" onClick={() => setPage("home")}>
          Urban<span>•</span>Thread
        </div>
        <div className="navbar-links">
          <button className={`nav-link ${page === "home" ? "active" : ""}`} onClick={() => setPage("home")}>Home</button>
          <button className={`nav-link ${page === "products" ? "active" : ""}`} onClick={() => setPage("products")}>Collection</button>
          {user && <button className={`nav-link ${page === "orders" ? "active" : ""}`} onClick={() => setPage("orders")}>Orders</button>}
        </div>
        <div className="navbar-actions">
          <button className="icon-btn" onClick={() => setPage("products")} title="Search">
            🔍
          </button>
          {user ? (
            <>
              <button className="icon-btn" onClick={() => setPage("cart")} title="Cart">
                🛍
                {cartCount > 0 && <span className="cart-badge">{cartCount > 9 ? "9+" : cartCount}</span>}
              </button>
              <button className="icon-btn" onClick={() => setPage("profile")} title="Profile">
                👤
              </button>
            </>
          ) : (
            <button className="btn btn-outline btn-sm" onClick={() => setPage("login")}>Sign in</button>
          )}
        </div>
      </div>
    </nav>
  );
}

// ─── Home Page ────────────────────────────────────────────────────────────────
function HomePage({ setPage, setSelectedProduct }) {
  const [featured, setFeatured] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/products/products/?limit=8`).then(r => r.ok ? r.json() : { results: [] }),
      fetch(`${API}/products/categories/?limit=6`).then(r => r.ok ? r.json() : { results: [] }),
    ]).then(([p, c]) => {
      setFeatured(p.results || []);
      setCategories(c.results || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleProduct = (product) => {
    setSelectedProduct(product);
    setPage("product-detail");
  };

  return (
    <div className="page">
      {/* Hero */}
      <div className="hero">
        <div className="container">
          <div className="hero-content">
            <p className="hero-eyebrow">New Collection — 2026</p>
            <h1 className="hero-title">Dressed for the<br /><em>Extraordinary</em></h1>
            <p className="hero-sub">Premium urban fashion crafted for those who refuse to blend in. Explore limited edition pieces.</p>
            <div className="flex gap-12">
              <button className="btn btn-gold btn-lg" onClick={() => setPage("products")}>Shop Now</button>
              <button className="btn btn-ghost btn-lg" style={{ color: "#fff", borderColor: "rgba(255,255,255,0.3)" }}
                onClick={() => setPage("products")}>View Lookbook</button>
            </div>
          </div>
        </div>
      </div>

      {/* Categories */}
      {categories.length > 0 && (
        <div className="section-sm" style={{ background: "var(--sand)" }}>
          <div className="container">
            <div className="flex gap-8" style={{ overflowX: "auto", paddingBottom: 4 }}>
              {categories.map(c => (
                <button key={c.id} className="filter-chip" onClick={() => setPage("products")}>
                  {c.category_name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Featured Products */}
      <div className="section">
        <div className="container">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 32 }}>
            <div>
              <p className="section-label">Curated Picks</p>
              <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 36, fontWeight: 300 }}>Featured Collection</h2>
            </div>
            <button className="btn btn-ghost" onClick={() => setPage("products")}>View All →</button>
          </div>
          {loading ? (
            <div className="loading-screen"><div className="spinner" /></div>
          ) : featured.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">👕</div>
              <h3 className="empty-title">No products yet</h3>
              <p className="empty-sub">Products will appear here once added.</p>
            </div>
          ) : (
            <div className="products-grid">
              {featured.map(p => <ProductCard key={p.id} product={p} onClick={() => handleProduct(p)} />)}
            </div>
          )}
        </div>
      </div>

      {/* Brand Banner */}
      <div style={{ background: "var(--ink)", padding: "60px 0" }}>
        <div className="container" style={{ textAlign: "center", color: "var(--white)" }}>
          <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--gold)", marginBottom: 16 }}>Our Promise</p>
          <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 40, fontWeight: 300, marginBottom: 16 }}>Quality without compromise</h2>
          <p style={{ color: "rgba(255,255,255,0.55)", maxWidth: 480, margin: "0 auto", fontSize: 14, lineHeight: 1.8 }}>
            Every piece in our collection is thoughtfully sourced, ethically made, and designed to outlast trends.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 48, marginTop: 40, flexWrap: "wrap" }}>
            {[["Premium", "Materials"], ["Ethical", "Production"], ["Free", "Returns"], ["Fast", "Delivery"]].map(([a, b]) => (
              <div key={a} style={{ textAlign: "center" }}>
                <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 28, color: "var(--gold)" }}>{a}</div>
                <div style={{ fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", marginTop: 4 }}>{b}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer style={{ background: "var(--white)", borderTop: "1px solid var(--sand3)", padding: "32px 0" }}>
        <div className="container" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
          <div className="navbar-logo">Urban<span style={{ color: "var(--gold)" }}>•</span>Thread</div>
          <p style={{ fontSize: 12, color: "var(--ink3)" }}>© 2026 Urban Thread. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

// ─── Product Card ─────────────────────────────────────────────────────────────
function ProductCard({ product, onClick }) {
  const hasDiscount = product.discount_price && product.discount_price > 0 && product.discount_price < product.price;
  const firstImg = product.images?.[0]?.image;

  return (
    <div className="product-card" onClick={onClick}>
      <div className="product-img">
        {firstImg ? <img src={`${API}${firstImg}`} alt={product.product_name} onError={e => { e.target.style.display = "none"; }} /> : <span>No Image</span>}
      </div>
      <div className="product-info">
        <p className="product-category">{product.category?.category_name}</p>
        <h3 className="product-name">{product.product_name}</h3>
        <div className="product-price">
          {hasDiscount ? (
            <>
              <span className="original">৳{Number(product.price).toLocaleString()}</span>
              <span className="discount">৳{Number(product.discount_price).toLocaleString()}</span>
            </>
          ) : (
            <span>৳{Number(product.price).toLocaleString()}</span>
          )}
        </div>
        {!product.is_available && <span className="badge badge-neutral mt-4">Out of stock</span>}
      </div>
    </div>
  );
}

// ─── Products Page ────────────────────────────────────────────────────────────
function ProductsPage({ setPage, setSelectedProduct }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [brandFilter, setBrandFilter] = useState("");
  const [sortBy, setSortBy] = useState("-created_at");
  const [page, setPageNum] = useState(0);
  const [total, setTotal] = useState(0);
  const LIMIT = 12;

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ limit: LIMIT, offset: page * LIMIT, ordering: sortBy });
    if (search) params.set("search", search);
    if (catFilter) params.set("category", catFilter);
    if (brandFilter) params.set("brand", brandFilter);
    try {
      const res = await fetch(`${API}/products/products/?${params}`);
      const data = await res.json();
      setProducts(data.results || []);
      setTotal(data.count || 0);
    } catch {}
    setLoading(false);
  }, [search, catFilter, brandFilter, sortBy, page]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  useEffect(() => {
    fetch(`${API}/products/categories/?limit=50`).then(r => r.json()).then(d => setCategories(d.results || [])).catch(() => {});
    fetch(`${API}/products/brands/?limit=50`).then(r => r.json()).then(d => setBrands(d.results || [])).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">Collection</h1>
          <p className="page-subtitle">{total} pieces available</p>
        </div>

        {/* Filters */}
        <div className="filters-bar">
          <input className="form-input" style={{ width: 220, height: 36 }} placeholder="Search products..." value={search}
            onChange={e => { setSearch(e.target.value); setPageNum(0); }} />
          <select className="form-select" style={{ width: 160, height: 36 }} value={catFilter}
            onChange={e => { setCatFilter(e.target.value); setPageNum(0); }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.category_name}</option>)}
          </select>
          <select className="form-select" style={{ width: 140, height: 36 }} value={brandFilter}
            onChange={e => { setBrandFilter(e.target.value); setPageNum(0); }}>
            <option value="">All Brands</option>
            {brands.map(b => <option key={b.id} value={b.id}>{b.brand_name}</option>)}
          </select>
          <select className="form-select" style={{ width: 160, height: 36 }} value={sortBy}
            onChange={e => setSortBy(e.target.value)}>
            <option value="-created_at">Newest First</option>
            <option value="price">Price: Low to High</option>
            <option value="-price">Price: High to Low</option>
            <option value="product_name">Name A–Z</option>
          </select>
          {(search || catFilter || brandFilter) && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(""); setCatFilter(""); setBrandFilter(""); setPageNum(0); }}>
              Clear Filters ✕
            </button>
          )}
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="loading-screen"><div className="spinner" /></div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3 className="empty-title">No products found</h3>
            <p className="empty-sub">Try adjusting your filters.</p>
          </div>
        ) : (
          <>
            <div className="products-grid">
              {products.map(p => (
                <ProductCard key={p.id} product={p} onClick={() => { setSelectedProduct(p); setPage("product-detail"); }} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="pagination">
                <button className="page-btn" disabled={page === 0} onClick={() => setPageNum(p => p - 1)}>‹</button>
                {Array.from({ length: totalPages }, (_, i) => (
                  <button key={i} className={`page-btn ${i === page ? "active" : ""}`} onClick={() => setPageNum(i)}>{i + 1}</button>
                ))}
                <button className="page-btn" disabled={page >= totalPages - 1} onClick={() => setPageNum(p => p + 1)}>›</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Product Detail ───────────────────────────────────────────────────────────
function ProductDetailPage({ product: initialProduct, setPage }) {
  const { user } = useAuth();
  const { addItem } = useCart();
  const toast = useToast();
  const [product] = useState(initialProduct);
  const [sizes, setSizes] = useState([]);
  const [colors, setColors] = useState([]);
  const [selectedSize, setSelectedSize] = useState(null);
  const [selectedColor, setSelectedColor] = useState(null);
  const [qty, setQty] = useState(1);
  const [activeImg, setActiveImg] = useState(0);
  const [inventory, setInventory] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewText, setReviewText] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [adding, setAdding] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const { authFetch } = useAuth();

  useEffect(() => {
    fetch(`${API}/products/sizes/`).then(r => r.json()).then(d => setSizes(d.results || d || [])).catch(() => {});
    fetch(`${API}/products/colors/`).then(r => r.json()).then(d => setColors(d.results || d || [])).catch(() => {});
    fetch(`${API}/reviews/?product_id=${product.id}`).then(r => r.json()).then(d => setReviews(d.results || d || [])).catch(() => {});
  }, [product.id]);

  useEffect(() => {
    if (selectedSize && selectedColor) {
      fetch(`${API}/inventory/inventorys/check_availability/?product_id=${product.id}&color_id=${selectedColor}&size_id=${selectedSize}`)
        .then(r => r.json()).then(setInventory).catch(() => {});
    }
  }, [selectedSize, selectedColor, product.id]);

  const hasDiscount = product.discount_price && product.discount_price > 0 && product.discount_price < product.price;
  const price = hasDiscount ? product.discount_price : product.price;
  const images = product.images || [];

  const handleAddToCart = async () => {
    if (!user) { setPage("login"); return; }
    if (!selectedSize) { toast("Please select a size", "error"); return; }
    if (!selectedColor) { toast("Please select a color", "error"); return; }
    setAdding(true);
    const res = await addItem(product.id, selectedColor, selectedSize, qty);
    if (res?.ok) toast("Added to cart!", "success");
    else { const d = await res?.json(); toast(d?.error || "Failed to add to cart", "error"); }
    setAdding(false);
  };

  const handleReview = async () => {
    if (!user) { setPage("login"); return; }
    setSubmittingReview(true);
    const res = await authFetch(`${API}/reviews/`, {
      method: "POST",
      body: JSON.stringify({ product: product.id, rating: reviewRating, review_text: reviewText })
    });
    if (res.ok) {
      const newReview = await res.json();
      setReviews(r => [newReview, ...r]);
      setReviewText(""); setReviewRating(5);
      toast("Review submitted!", "success");
    } else toast("Failed to submit review", "error");
    setSubmittingReview(false);
  };

  const avgRating = reviews.length > 0 ? (reviews.reduce((s, r) => s + r.rating, 0) / reviews.length).toFixed(1) : null;

  return (
    <div className="page">
      <div className="container">
        <div style={{ padding: "16px 0" }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage("products")}>← Back</button>
        </div>
        <div className="detail-grid">
          {/* Images */}
          <div className="detail-images">
            <div className="main-image">
              {images[activeImg]?.image
                ? <img src={`${API}${images[activeImg].image}`} alt={product.product_name} />
                : <span style={{ color: "var(--ink3)" }}>No image available</span>}
            </div>
            {images.length > 1 && (
              <div className="thumb-list">
                {images.map((img, i) => (
                  <div key={i} className={`thumb ${i === activeImg ? "active" : ""}`} onClick={() => setActiveImg(i)}>
                    {img.image && <img src={`${API}${img.image}`} alt="" />}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="detail-info">
            <div>
              <p className="detail-brand">{product.brand?.brand_name}</p>
              <h1 className="detail-name">{product.product_name}</h1>
              {avgRating && (
                <div className="flex gap-8 mt-8" style={{ alignItems: "center" }}>
                  <Stars rating={Math.round(Number(avgRating))} />
                  <span className="text-sm text-muted">{avgRating} ({reviews.length} reviews)</span>
                </div>
              )}
            </div>

            <div className="detail-price">
              {hasDiscount ? (
                <>
                  <span className="old-price">৳{Number(product.price).toLocaleString()}</span>
                  <span className="main-price">৳{Number(product.discount_price).toLocaleString()}</span>
                  <span className="badge badge-gold save-badge">SAVE {Math.round((1 - product.discount_price / product.price) * 100)}%</span>
                </>
              ) : (
                <span className="main-price">৳{Number(product.price).toLocaleString()}</span>
              )}
            </div>

            <div className="divider" />

            {/* Colors */}
            {colors.length > 0 && (
              <div>
                <div className="section-label">Color {selectedColor && <span style={{ color: "var(--ink)", textTransform: "none", letterSpacing: 0 }}>— {colors.find(c => c.id === selectedColor)?.color}</span>}</div>
                <div className="color-grid mt-8">
                  {colors.map(c => (
                    <button key={c.id} className={`color-btn ${selectedColor === c.id ? "selected" : ""}`}
                      style={{ background: c.color.toLowerCase().replace(/\s/g, "") || "#ccc" }}
                      title={c.color} onClick={() => setSelectedColor(c.id)} />
                  ))}
                </div>
              </div>
            )}

            {/* Sizes */}
            {sizes.length > 0 && (
              <div>
                <div className="section-label">Size</div>
                <div className="size-grid mt-8">
                  {sizes.map(s => (
                    <button key={s.id} className={`size-btn ${selectedSize === s.id ? "selected" : ""}`}
                      onClick={() => setSelectedSize(s.id)}>{s.size_type}</button>
                  ))}
                </div>
              </div>
            )}

            {/* Stock indicator */}
            {inventory !== null && (
              <div>
                {inventory.available
                  ? <span className="badge badge-success inventory-badge">In Stock ({inventory.quantity} available)</span>
                  : <span className="badge badge-danger inventory-badge">Out of Stock</span>}
              </div>
            )}

            {/* Quantity */}
            <div>
              <div className="section-label">Quantity</div>
              <div className="qty-control mt-8">
                <button className="qty-btn" onClick={() => setQty(q => Math.max(1, q - 1))}>−</button>
                <span className="qty-val">{qty}</span>
                <button className="qty-btn" onClick={() => setQty(q => Math.min(inventory?.quantity || 99, q + 1))}>+</button>
              </div>
            </div>

            {/* CTA */}
            <div className="flex gap-12">
              <button className="btn btn-primary btn-lg" style={{ flex: 1 }}
                onClick={handleAddToCart} disabled={adding || (inventory && !inventory.available)}>
                {adding ? <><div className="spinner-sm" style={{ borderTopColor: "#fff" }} /> Adding...</> : "Add to Cart"}
              </button>
            </div>

            <div className="divider" />

            {/* Description */}
            {product.description && (
              <div>
                <div className="section-label">Description</div>
                <p className="text-sm mt-8" style={{ color: "var(--ink2)", lineHeight: 1.8 }}>{product.description}</p>
              </div>
            )}

            {/* Specs */}
            <div>
              <div className="section-label">Details</div>
              <div className="mt-8">
                <div className="spec-row"><span className="spec-label">Category</span><span>{product.category?.category_name || "—"}</span></div>
                <div className="spec-row"><span className="spec-label">Brand</span><span>{product.brand?.brand_name || "—"}</span></div>
                <div className="spec-row"><span className="spec-label">Availability</span><span>{product.is_available ? "Available" : "Unavailable"}</span></div>
                <div className="spec-row"><span className="spec-label">SKU</span><span>#{product.id}</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Reviews */}
        <div className="section" style={{ borderTop: "1px solid var(--sand3)" }}>
          <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 28, marginBottom: 24 }}>
            Customer Reviews {reviews.length > 0 && <span style={{ fontSize: 18, color: "var(--ink3)" }}>({reviews.length})</span>}
          </h2>
          {user && (
            <div className="card card-body" style={{ marginBottom: 24 }}>
              <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 20, marginBottom: 16 }}>Write a Review</h3>
              <div className="form-group">
                <div className="section-label">Rating</div>
                <div className="flex gap-8 mt-4">
                  {[1,2,3,4,5].map(i => (
                    <button key={i} onClick={() => setReviewRating(i)}
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: 24, color: i <= reviewRating ? "var(--gold)" : "var(--sand3)" }}>★</button>
                  ))}
                </div>
              </div>
              <div className="form-group mt-16">
                <textarea className="form-textarea" value={reviewText} onChange={e => setReviewText(e.target.value)} placeholder="Share your thoughts about this product..." />
              </div>
              <button className="btn btn-primary mt-16" onClick={handleReview} disabled={submittingReview || !reviewText.trim()}>
                {submittingReview ? "Submitting..." : "Submit Review"}
              </button>
            </div>
          )}
          {reviews.length === 0 ? (
            <p className="text-muted text-sm">No reviews yet. Be the first!</p>
          ) : (
            reviews.map(r => (
              <div key={r.id} className="review-card">
                <div className="review-header">
                  <div>
                    <div className="fw-500" style={{ fontSize: 14 }}>{r.user?.username || "Customer"}</div>
                    <Stars rating={r.rating} />
                  </div>
                  <span className="text-xs text-muted">{new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                <p className="text-sm mt-8">{r.review_text}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Cart Page ────────────────────────────────────────────────────────────────
function CartPage({ setPage }) {
  const { cart, loading, removeItem, updateItem, clearCart } = useCart();
  const toast = useToast();
  const [coupon, setCoupon] = useState("");
  const [discount, setDiscount] = useState(null);
  const [validatingCoupon, setValidatingCoupon] = useState(false);
  const { authFetch } = useAuth();

  const handleRemove = async (id) => {
    await removeItem(id);
    toast("Item removed", "success");
  };

  const handleQty = async (item, newQty) => {
    if (newQty < 1) { await removeItem(item.id); return; }
    const res = await updateItem(item.id, newQty);
    if (!res?.ok) { const d = await res?.json(); toast(d?.error || "Update failed", "error"); }
  };

  const validateCoupon = async () => {
    if (!coupon.trim()) return;
    setValidatingCoupon(true);
    try {
      const res = await authFetch(`${API}/coupons/validate_coupon/`, {
        method: "POST", body: JSON.stringify({ code: coupon })
      });
      const data = await res.json();
      if (res.ok && data.valid) { setDiscount(data); toast(`Coupon applied! ${data.discount}% off`, "success"); }
      else toast(data.error || "Invalid coupon", "error");
    } catch { toast("Error validating coupon", "error"); }
    setValidatingCoupon(false);
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  const items = cart?.items || [];
  const subtotal = cart?.total_amount || 0;
  const discountAmt = discount ? (subtotal * discount.discount / 100) : 0;
  const total = subtotal - discountAmt;

  if (items.length === 0) {
    return (
      <div className="page container">
        <div className="page-header"><h1 className="page-title">Shopping Cart</h1></div>
        <div className="empty-state">
          <div className="empty-icon">🛍</div>
          <h3 className="empty-title">Your cart is empty</h3>
          <p className="empty-sub">Add some items to get started</p>
          <button className="btn btn-primary mt-24" onClick={() => setPage("products")}>Browse Collection</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">Shopping Cart</h1>
          <p className="page-subtitle">{items.length} item{items.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="cart-layout">
          {/* Items */}
          <div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
              <button className="btn btn-ghost btn-sm" onClick={async () => { await clearCart(); toast("Cart cleared"); }}>
                Clear All
              </button>
            </div>
            {items.map(item => (
              <div key={item.id} className="cart-item-row">
                <div className="cart-item-img">
                  {item.product?.images?.[0]?.image
                    ? <img src={`${API}${item.product.images[0].image}`} alt="" />
                    : null}
                </div>
                <div>
                  <p className="cart-item-name">{item.product?.product_name}</p>
                  <p className="cart-item-meta mt-4">
                    {item.color?.color} · {item.size?.size_type}
                  </p>
                  <p className="fw-500 mt-8">
                    ৳{Number(item.subtotal || (item.quantity * (item.product?.discount_price || item.product?.price || 0))).toLocaleString()}
                  </p>
                  <div className="qty-control mt-8">
                    <button className="qty-btn" onClick={() => handleQty(item, item.quantity - 1)}>−</button>
                    <span className="qty-val">{item.quantity}</span>
                    <button className="qty-btn" onClick={() => handleQty(item, item.quantity + 1)}>+</button>
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => handleRemove(item.id)} style={{ color: "var(--danger)" }}>✕</button>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div>
            <div className="cart-summary">
              <h2 className="summary-title">Order Summary</h2>
              <div className="coupon-row">
                <input className="form-input" value={coupon} onChange={e => setCoupon(e.target.value.toUpperCase())} placeholder="Coupon code" />
                <button className="btn btn-outline btn-sm" onClick={validateCoupon} disabled={validatingCoupon}>Apply</button>
              </div>
              {discount && <p className="text-sm" style={{ color: "var(--success)", marginBottom: 12 }}>✓ {discount.message}</p>}
              <div className="summary-row"><span>Subtotal</span><span>৳{subtotal.toLocaleString()}</span></div>
              {discountAmt > 0 && <div className="summary-row" style={{ color: "var(--success)" }}><span>Discount</span><span>−৳{discountAmt.toFixed(0)}</span></div>}
              <div className="summary-row"><span>Shipping</span><span className="text-gold">Free</span></div>
              <div className="summary-total">
                <span className="fw-500">Total</span>
                <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22 }}>৳{total.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</span>
              </div>
              <button className="btn btn-primary btn-full mt-16 btn-lg"
                onClick={() => setPage("checkout", { discount })}>
                Proceed to Checkout →
              </button>
              <button className="btn btn-ghost btn-full mt-8" onClick={() => setPage("products")}>
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Checkout Page ────────────────────────────────────────────────────────────
function CheckoutPage({ setPage, extra }) {
  const { authFetch, user } = useAuth();
  const { cart, fetchCart } = useCart();
  const toast = useToast();
  const [addresses, setAddresses] = useState([]);
  const [selectedAddr, setSelectedAddr] = useState(null);
  const [payMethod, setPayMethod] = useState("cash_on_delivery");
  const [placing, setPlacing] = useState(false);
  const [newAddr, setNewAddr] = useState({ full_name: "", city: "", state: "", pincode: "", phone: "", address: "" });
  const [showNewAddr, setShowNewAddr] = useState(false);
  const [savingAddr, setSavingAddr] = useState(false);

  useEffect(() => {
    authFetch(`${API}/accounts/address/`).then(r => r.json()).then(d => {
      const list = d.results || d || [];
      setAddresses(list);
      if (list.length > 0) setSelectedAddr(list[0].id);
      else setShowNewAddr(true);
    }).catch(() => {});
  }, []);

  const saveAddress = async () => {
    setSavingAddr(true);
    const res = await authFetch(`${API}/accounts/address/`, { method: "POST", body: JSON.stringify(newAddr) });
    if (res.ok) {
      const addr = await res.json();
      setAddresses(a => [...a, addr]);
      setSelectedAddr(addr.id);
      setShowNewAddr(false);
      toast("Address saved", "success");
    } else toast("Failed to save address", "error");
    setSavingAddr(false);
  };

  const placeOrder = async () => {
    if (!selectedAddr) { toast("Please select a delivery address", "error"); return; }
    if (!cart?.items?.length) { toast("Your cart is empty", "error"); return; }
    setPlacing(true);
    const body = { address_id: selectedAddr, payment_method: payMethod };
    if (extra?.discount?.code) body.coupon_code = extra.discount.code;
    try {
      const res = await authFetch(`${API}/orders/create_order/`, { method: "POST", body: JSON.stringify(body) });
      const data = await res.json();
      if (res.ok) {
        toast("Order placed successfully!", "success");
        await fetchCart();
        setPage("orders");
      } else {
        toast(data.error || "Failed to place order", "error");
      }
    } catch { toast("Network error", "error"); }
    setPlacing(false);
  };

  const total = cart?.total_amount || 0;
  const discount = extra?.discount;
  const discountAmt = discount ? (total * discount.discount / 100) : 0;
  const finalTotal = total - discountAmt;

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">Checkout</h1>
        </div>
        <div className="checkout-layout">
          <div>
            {/* Delivery Address */}
            <div className="card card-body" style={{ marginBottom: 24 }}>
              <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22, marginBottom: 16 }}>Delivery Address</h3>
              {addresses.map(a => (
                <div key={a.id} className={`address-card ${selectedAddr === a.id ? "selected" : ""}`}
                  onClick={() => setSelectedAddr(a.id)} style={{ cursor: "pointer" }}>
                  <div className="flex gap-8" style={{ alignItems: "flex-start" }}>
                    <input type="radio" checked={selectedAddr === a.id} onChange={() => setSelectedAddr(a.id)} style={{ marginTop: 3 }} />
                    <div>
                      <p className="fw-500">{a.full_name}</p>
                      <p className="text-sm text-muted mt-4">{a.address}, {a.city}, {a.state} {a.pincode}</p>
                      <p className="text-sm text-muted">📞 {a.phone}</p>
                    </div>
                  </div>
                </div>
              ))}
              <button className="btn btn-ghost btn-sm mt-8" onClick={() => setShowNewAddr(!showNewAddr)}>
                {showNewAddr ? "Cancel" : "+ Add New Address"}
              </button>
              {showNewAddr && (
                <div className="form-stack mt-16">
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Full Name</label>
                      <input className="form-input" value={newAddr.full_name} onChange={e => setNewAddr(a => ({ ...a, full_name: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Phone</label>
                      <input className="form-input" value={newAddr.phone} onChange={e => setNewAddr(a => ({ ...a, phone: e.target.value }))} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Address</label>
                    <textarea className="form-textarea" value={newAddr.address} onChange={e => setNewAddr(a => ({ ...a, address: e.target.value }))} style={{ minHeight: 60 }} />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">City</label>
                      <input className="form-input" value={newAddr.city} onChange={e => setNewAddr(a => ({ ...a, city: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">State / District</label>
                      <input className="form-input" value={newAddr.state} onChange={e => setNewAddr(a => ({ ...a, state: e.target.value }))} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Postal Code</label>
                    <input className="form-input" value={newAddr.pincode} onChange={e => setNewAddr(a => ({ ...a, pincode: e.target.value }))} />
                  </div>
                  <button className="btn btn-outline" onClick={saveAddress} disabled={savingAddr}>
                    {savingAddr ? "Saving..." : "Save Address"}
                  </button>
                </div>
              )}
            </div>

            {/* Payment Method */}
            <div className="card card-body">
              <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22, marginBottom: 16 }}>Payment Method</h3>
              {[
                { value: "cash_on_delivery", label: "Cash on Delivery", icon: "💵", desc: "Pay when you receive your order" },
                { value: "sslcommerz", label: "SSLCommerz", icon: "💳", desc: "Secure online payment" },
              ].map(m => (
                <div key={m.value}
                  className={`address-card ${payMethod === m.value ? "selected" : ""}`}
                  onClick={() => setPayMethod(m.value)} style={{ cursor: "pointer", marginBottom: 12 }}>
                  <div className="flex gap-12" style={{ alignItems: "center" }}>
                    <input type="radio" checked={payMethod === m.value} onChange={() => setPayMethod(m.value)} />
                    <span style={{ fontSize: 20 }}>{m.icon}</span>
                    <div>
                      <p className="fw-500">{m.label}</p>
                      <p className="text-xs text-muted">{m.desc}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Order Summary */}
          <div>
            <div className="cart-summary">
              <h2 className="summary-title">Order Summary</h2>
              {cart?.items?.map(item => (
                <div key={item.id} className="flex gap-12 mt-8" style={{ alignItems: "center" }}>
                  <div style={{ flex: 1 }}>
                    <p className="text-sm fw-500">{item.product?.product_name}</p>
                    <p className="text-xs text-muted">{item.color?.color} · {item.size?.size_type} × {item.quantity}</p>
                  </div>
                  <span className="text-sm">৳{Number(item.subtotal || 0).toLocaleString()}</span>
                </div>
              ))}
              <div className="divider" style={{ margin: "16px 0" }} />
              <div className="summary-row"><span>Subtotal</span><span>৳{total.toLocaleString()}</span></div>
              {discountAmt > 0 && <div className="summary-row" style={{ color: "var(--success)" }}><span>Discount</span><span>−৳{discountAmt.toFixed(0)}</span></div>}
              <div className="summary-row"><span>Shipping</span><span className="text-gold">Free</span></div>
              <div className="summary-total">
                <span className="fw-500">Total</span>
                <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22 }}>৳{finalTotal.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</span>
              </div>
              <button className="btn btn-primary btn-full mt-16 btn-lg" onClick={placeOrder} disabled={placing}>
                {placing ? <><div className="spinner-sm" style={{ borderTopColor: "#fff" }} /> Placing Order...</> : "Place Order →"}
              </button>
              <button className="btn btn-ghost btn-full mt-8" onClick={() => setPage("cart")}>← Back to Cart</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Orders Page ──────────────────────────────────────────────────────────────
function OrdersPage({ setPage }) {
  const { authFetch } = useAuth();
  const toast = useToast();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${API}/orders/order_history/`);
      if (res.ok) setOrders(await res.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchOrders(); }, []);

  const cancelOrder = async (id) => {
    const res = await authFetch(`${API}/orders/${id}/cancel_order/`, { method: "PATCH" });
    if (res.ok) { toast("Order cancelled", "success"); fetchOrders(); }
    else { const d = await res.json(); toast(d.error || "Cannot cancel order", "error"); }
  };

  const statusColor = (s) => {
    if (s === "completed") return "badge-success";
    if (s === "cancelled") return "badge-danger";
    if (s === "processing") return "badge-gold";
    return "badge-neutral";
  };

  const payColor = (s) => {
    if (s === "paid") return "badge-success";
    if (s === "refunded") return "badge-warning";
    if (s === "unpaid") return "badge-neutral";
    return "badge-neutral";
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">My Orders</h1>
          <p className="page-subtitle">{orders.length} order{orders.length !== 1 ? "s" : ""}</p>
        </div>
        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📦</div>
            <h3 className="empty-title">No orders yet</h3>
            <p className="empty-sub">Start shopping to see your orders here</p>
            <button className="btn btn-primary mt-24" onClick={() => setPage("products")}>Browse Collection</button>
          </div>
        ) : (
          orders.map(order => (
            <div key={order.id} className="order-card">
              <div className="order-header">
                <div>
                  <p className="order-number">{order.order_number}</p>
                  <p className="order-date text-xs text-muted mt-4">{new Date(order.created_at).toLocaleDateString("en-BD", { day: "numeric", month: "long", year: "numeric" })}</p>
                </div>
                <div className="flex gap-8" style={{ flexWrap: "wrap", justifyContent: "flex-end" }}>
                  <span className={`badge ${statusColor(order.order_status)}`}>{order.order_status}</span>
                  <span className={`badge ${payColor(order.payment_status)}`}>{order.payment_status}</span>
                </div>
              </div>
              <div className="order-items-list">
                {(order.items || []).map(item => (
                  <div key={item.id} className="order-item">
                    <div className="order-item-img">
                      {item.product?.images?.[0]?.image && <img src={`${API}${item.product.images[0].image}`} alt="" />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <p className="text-sm fw-500">{item.product?.product_name}</p>
                      <p className="text-xs text-muted">{item.color?.color} · {item.size?.size_type} × {item.quantity}</p>
                    </div>
                    <span className="text-sm fw-500">৳{Number(item.price * item.quantity).toLocaleString()}</span>
                  </div>
                ))}
              </div>
              <div className="order-footer">
                <div>
                  <span className="text-sm text-muted">Total: </span>
                  <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 20, fontWeight: 500 }}>
                    ৳{Number(order.total_amount).toLocaleString()}
                  </span>
                </div>
                {["pending", "processing"].includes(order.order_status) && (
                  <button className="btn btn-outline btn-sm" style={{ color: "var(--danger)", borderColor: "var(--danger)" }}
                    onClick={() => cancelOrder(order.id)}>Cancel Order</button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ─── Profile Page ─────────────────────────────────────────────────────────────
function ProfilePage({ setPage }) {
  const { user, authFetch, logout, updateUser } = useAuth();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState("account");
  const [addresses, setAddresses] = useState([]);
  const [payments, setPayments] = useState([]);
  const [editForm, setEditForm] = useState({ username: user?.username || "", email: user?.email || "" });
  const [newAddr, setNewAddr] = useState({ full_name: "", city: "", state: "", pincode: "", phone: "", address: "" });
  const [savingAddr, setSavingAddr] = useState(false);

  useEffect(() => {
    if (activeTab === "addresses") {
      authFetch(`${API}/accounts/address/`).then(r => r.json()).then(d => setAddresses(d.results || d || [])).catch(() => {});
    }
    if (activeTab === "payments") {
      authFetch(`${API}/payments/my_payments/`).then(r => r.json()).then(d => setPayments(d.results || d || [])).catch(() => {});
    }
  }, [activeTab, authFetch]);

  const [savingProfile, setSavingProfile] = useState(false);

  const saveProfile = async () => {
    setSavingProfile(true);
    const payload = { username: editForm.username, email: editForm.email };
    const endpoints = [`${API}/accounts/profile/`, `${API}/accounts/me/`];
    let ok = false;
    let data = null;

    for (const url of endpoints) {
      try {
        const res = await authFetch(url, { method: "PATCH", body: JSON.stringify(payload) });
        if (res.ok) {
          data = await res.json();
          ok = true;
          break;
        }
      } catch {}
    }

    if (ok) {
      updateUser({
        username: data?.username ?? payload.username,
        email: data?.email ?? payload.email,
      });
      toast("Profile updated!", "success");
    } else {
      toast("Profile update endpoint not found (tried /accounts/profile/ and /accounts/me/)", "error");
    }
    setSavingProfile(false);
  };

  const saveAddress = async () => {
    setSavingAddr(true);
    const res = await authFetch(`${API}/accounts/address/`, { method: "POST", body: JSON.stringify(newAddr) });
    if (res.ok) {
      const addr = await res.json();
      setAddresses(a => [...a, addr]);
      setNewAddr({ full_name: "", city: "", state: "", pincode: "", phone: "", address: "" });
      toast("Address saved!", "success");
    } else toast("Failed to save address", "error");
    setSavingAddr(false);
  };

  const deleteAddress = async (id) => {
    await authFetch(`${API}/accounts/address/${id}/`, { method: "DELETE" });
    setAddresses(a => a.filter(x => x.id !== id));
    toast("Address removed");
  };

  const tabs = [
    { key: "account", label: "Account Info", icon: "👤" },
    { key: "addresses", label: "Addresses", icon: "📍" },
    { key: "payments", label: "Payment History", icon: "💳" },
  ];

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">My Account</h1>
          <p className="page-subtitle">Welcome back, {user?.username}</p>
        </div>
        <div className="profile-layout">
          <div className="profile-nav">
            {tabs.map(t => (
              <button key={t.key} className={`profile-nav-link ${activeTab === t.key ? "active" : ""}`}
                onClick={() => setActiveTab(t.key)}>
                <span>{t.icon}</span> {t.label}
              </button>
            ))}
            <div style={{ height: 1, background: "var(--sand3)", margin: "8px 0" }} />
            <button className="profile-nav-link" style={{ color: "var(--danger)" }}
              onClick={() => { logout(); setPage("home"); }}>
              <span>🚪</span> Sign Out
            </button>
          </div>

          <div>
            {activeTab === "account" && (
              <div>
                <h2 className="profile-section-title">Account Information</h2>
                <div className="card card-body">
                  <div className="form-stack">
                    <div className="form-group">
                      <label className="form-label">Username</label>
                      <input className="form-input" value={editForm.username} onChange={e => setEditForm(f => ({ ...f, username: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Email</label>
                      <input className="form-input" type="email" value={editForm.email} onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Account Type</label>
                      <input className="form-input" value={user?.is_staff ? "Admin" : "Customer"} readOnly style={{ background: "var(--sand)", cursor: "not-allowed" }} />
                    </div>
                    <div>
                      <button className="btn btn-primary" onClick={saveProfile} disabled={savingProfile}>
                        {savingProfile ? "Saving..." : "Save Changes"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "addresses" && (
              <div>
                <h2 className="profile-section-title">Saved Addresses</h2>
                {addresses.map(a => (
                  <div key={a.id} className="address-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <p className="fw-500">{a.full_name}</p>
                        <p className="text-sm text-muted mt-4">{a.address}</p>
                        <p className="text-sm text-muted">{a.city}, {a.state} {a.pincode}</p>
                        <p className="text-sm text-muted">📞 {a.phone}</p>
                      </div>
                      <button className="btn btn-ghost btn-sm" style={{ color: "var(--danger)" }}
                        onClick={() => deleteAddress(a.id)}>Delete</button>
                    </div>
                  </div>
                ))}
                <div className="card card-body mt-16">
                  <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 20, marginBottom: 16 }}>Add New Address</h3>
                  <div className="form-stack">
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <input className="form-input" value={newAddr.full_name} onChange={e => setNewAddr(a => ({ ...a, full_name: e.target.value }))} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Phone</label>
                        <input className="form-input" value={newAddr.phone} onChange={e => setNewAddr(a => ({ ...a, phone: e.target.value }))} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Street Address</label>
                      <textarea className="form-textarea" value={newAddr.address} onChange={e => setNewAddr(a => ({ ...a, address: e.target.value }))} style={{ minHeight: 60 }} />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">City</label>
                        <input className="form-input" value={newAddr.city} onChange={e => setNewAddr(a => ({ ...a, city: e.target.value }))} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">State</label>
                        <input className="form-input" value={newAddr.state} onChange={e => setNewAddr(a => ({ ...a, state: e.target.value }))} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Postal Code</label>
                      <input className="form-input" value={newAddr.pincode} onChange={e => setNewAddr(a => ({ ...a, pincode: e.target.value }))} style={{ maxWidth: 180 }} />
                    </div>
                    <button className="btn btn-primary" onClick={saveAddress} disabled={savingAddr}>
                      {savingAddr ? "Saving..." : "Save Address"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "payments" && (
              <div>
                <h2 className="profile-section-title">Payment History</h2>
                {payments.length === 0 ? (
                  <div className="empty-state" style={{ padding: "40px 0" }}>
                    <div className="empty-icon">💳</div>
                    <h3 className="empty-title">No payments yet</h3>
                  </div>
                ) : payments.map(p => (
                  <div key={p.id} className="order-card">
                    <div className="order-header">
                      <div>
                        <p className="text-sm fw-500" style={{ fontFamily: "monospace" }}>{p.transaction_id}</p>
                        <p className="order-date text-xs text-muted">{new Date(p.created_at).toLocaleDateString()}</p>
                        <p className="text-sm text-muted mt-4">{p.payment_method_display}</p>
                      </div>
                      <div>
                        <span className={`badge ${p.status === "completed" ? "badge-success" : p.status === "failed" ? "badge-danger" : "badge-neutral"}`}>{p.status}</span>
                        <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22, marginTop: 8 }}>৳{Number(p.amount).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Login / Register ─────────────────────────────────────────────────────────
function AuthPage({ setPage, defaultMode = "login" }) {
  const [mode, setMode] = useState(defaultMode);
  const { login } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs = {};
    if (!form.email) errs.email = "Email is required";
    if (!form.password) errs.password = "Password is required";
    if (mode === "register" && !form.username) errs.username = "Username is required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setLoading(true);
    const url = mode === "login" ? `${API}/accounts/login/` : `${API}/accounts/register/`;
    const body = mode === "login" ? { email: form.email, password: form.password } : form;
    try {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json();
      if (res.ok) {
        login({ id: data.id, username: data.username, email: data.email, is_staff: data.is_staff, is_superuser: data.is_superuser }, data.tokens);
        toast(`Welcome${mode === "login" ? " back" : ""}!`, "success");
        setPage("home");
      } else {
        const errMsg = data.non_field_errors?.[0] || data.email?.[0] || data.username?.[0] || data.password?.[0] || "Authentication failed";
        toast(errMsg, "error");
      }
    } catch { toast("Network error", "error"); }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>Urban<span>•</span>Thread</h1>
          <p className="text-muted text-sm" style={{ marginTop: 4 }}>{mode === "login" ? "Sign in to your account" : "Create your account"}</p>
        </div>
        <div className="form-stack">
          {mode === "register" && (
            <div className="form-group">
              <label className="form-label">Username</label>
              <input className="form-input" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} placeholder="johndoe" />
              {errors.username && <span className="form-error">{errors.username}</span>}
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} placeholder="you@example.com" />
            {errors.email && <span className="form-error">{errors.email}</span>}
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="••••••••" onKeyDown={e => e.key === "Enter" && handleSubmit()} />
            {errors.password && <span className="form-error">{errors.password}</span>}
          </div>
          <button className="btn btn-primary btn-full btn-lg" onClick={handleSubmit} disabled={loading}>
            {loading ? <><div className="spinner-sm" style={{ borderTopColor: "#fff" }} /> Please wait...</> : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </div>
        <div className="auth-switch">
          {mode === "login" ? (
            <p>Don't have an account? <button onClick={() => setMode("register")}>Create one</button></p>
          ) : (
            <p>Already have an account? <button onClick={() => setMode("login")}>Sign in</button></p>
          )}
        </div>
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage("home")}>← Back to home</button>
        </div>
      </div>
    </div>
  );
}

// ─── Router / App Shell ───────────────────────────────────────────────────────
function AppShell() {
  const [page, setPageRaw] = useState("home");
  const [pageExtra, setPageExtra] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const { user } = useAuth();

  const setPage = (p, extra = null) => {
    setPageRaw(p);
    setPageExtra(extra);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const renderPage = () => {
    switch (page) {
      case "home": return <HomePage setPage={setPage} setSelectedProduct={setSelectedProduct} />;
      case "products": return <ProductsPage setPage={setPage} setSelectedProduct={setSelectedProduct} />;
      case "product-detail": return selectedProduct
        ? <ProductDetailPage product={selectedProduct} setPage={setPage} />
        : <ProductsPage setPage={setPage} setSelectedProduct={setSelectedProduct} />;
      case "cart": return user ? <CartPage setPage={setPage} /> : <AuthPage setPage={setPage} />;
      case "checkout": return user ? <CheckoutPage setPage={setPage} extra={pageExtra} /> : <AuthPage setPage={setPage} />;
      case "orders": return user ? <OrdersPage setPage={setPage} /> : <AuthPage setPage={setPage} />;
      case "profile": return user ? <ProfilePage setPage={setPage} /> : <AuthPage setPage={setPage} />;
      case "login": return <AuthPage setPage={setPage} defaultMode="login" />;
      case "register": return <AuthPage setPage={setPage} defaultMode="register" />;
      default: return <HomePage setPage={setPage} setSelectedProduct={setSelectedProduct} />;
    }
  };

  const hideNav = ["login", "register"].includes(page);

  return (
    <>
      {!hideNav && <Navbar page={page} setPage={setPage} />}
      {renderPage()}
    </>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      <style>{styles}</style>
      <AuthProvider>
        <ToastProvider>
          <CartProvider>
            <AppShell />
          </CartProvider>
        </ToastProvider>
      </AuthProvider>
    </>
  );
}
