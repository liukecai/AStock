import { reactive } from "vue";
import { api } from "./api";

const STORAGE_KEY = "aquant_admin_secret";

export const adminAuth = reactive({
  required: false,
  authorized: false,
  loading: false,
  error: "",
  dialogOpen: false,
});

function storedSecret() {
  return window.localStorage.getItem(STORAGE_KEY) || "";
}

function saveSecret(secret) {
  window.localStorage.setItem(STORAGE_KEY, secret);
}

function clearSecret() {
  window.localStorage.removeItem(STORAGE_KEY);
}

export function getAdminSecret() {
  return storedSecret();
}

export async function bootstrapAdminAuth() {
  adminAuth.loading = true;
  adminAuth.error = "";
  try {
    const status = await api.getAdminAuthStatus();
    adminAuth.required = Boolean(status.required);
    if (!adminAuth.required) {
      adminAuth.authorized = true;
      return;
    }

    const secret = storedSecret();
    if (!secret) {
      adminAuth.authorized = false;
      return;
    }

    await api.authorizeAdmin(secret);
    adminAuth.authorized = true;
  } catch (err) {
    clearSecret();
    adminAuth.authorized = false;
    adminAuth.error = err.message;
  } finally {
    adminAuth.loading = false;
  }
}

export async function authorizeAdmin(secret) {
  adminAuth.loading = true;
  adminAuth.error = "";
  try {
    await api.authorizeAdmin(secret);
    saveSecret(secret);
    adminAuth.required = true;
    adminAuth.authorized = true;
    adminAuth.dialogOpen = false;
  } catch (err) {
    adminAuth.authorized = false;
    adminAuth.error = err.message;
    throw err;
  } finally {
    adminAuth.loading = false;
  }
}

export function logoutAdmin() {
  clearSecret();
  adminAuth.authorized = !adminAuth.required;
  adminAuth.dialogOpen = false;
  adminAuth.error = "";
}

export function openAdminDialog() {
  adminAuth.error = "";
  adminAuth.dialogOpen = true;
}

export function closeAdminDialog() {
  adminAuth.dialogOpen = false;
  adminAuth.error = "";
}
