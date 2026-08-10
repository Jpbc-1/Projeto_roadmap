import * as SecureStore from 'expo-secure-store';

// Token storage lives here, and only here — nothing else in the app should
// import `expo-secure-store` directly. That way there's exactly one place
// to change if the storage mechanism ever changes again.
//
// Why SecureStore instead of AsyncStorage: AsyncStorage writes plain,
// unencrypted text to disk (on Android it's a world-readable-by-the-app
// XML/SQLite file; on iOS a plist) — fine for UI preferences, not for an
// auth token, which is effectively a password-equivalent bearer credential.
// SecureStore uses Keychain on iOS and Keystore-backed EncryptedSharedPreferences
// on Android, so the token is encrypted at rest by the OS.
const TOKEN_KEY = 'roadmap_ai_access_token';

export async function getToken(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    // A locked/unavailable keystore (rare, but happens right after a
    // device restart on some Android versions) should read as "not
    // logged in", not crash whatever screen asked for the token.
    console.warn('authStorage: failed to read token', error);
    return null;
  }
}

export async function setToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function deleteToken(): Promise<void> {
  try {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
  } catch (error) {
    // Deleting something that isn't there shouldn't be a crash-worthy
    // error during logout.
    console.warn('authStorage: failed to delete token', error);
  }
}
