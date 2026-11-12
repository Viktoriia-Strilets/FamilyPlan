import { useCallback, useEffect, useState } from 'react';
import {
  loginUser,
  registerUser,
  completeGoogleRegistration,
  createGoogleLinkToken,
  getGoogleLinkUrl,
} from '../api/authService';
import { getCurrentUser, getUsers, updateUser, deleteUser } from '../api/userService';
import { getFamilies, createFamily, updateFamily, deleteFamily } from '../api/familyService';


const emptyUser = {
  token: null, role: null, username: '', userId: '', familyId: '',
  inviteCode: '', familyName: '', hasPassword: false,
};

function readStoredUser() {
  return {
    token: sessionStorage.getItem('token'),
    role: sessionStorage.getItem('role'),
    username: sessionStorage.getItem('username') || '',
    userId: sessionStorage.getItem('user_id') || '',
    familyId: sessionStorage.getItem('family_id') || '',
    inviteCode: sessionStorage.getItem('invite_code') || '',
    familyName: sessionStorage.getItem('family_name') || '',
    hasPassword: sessionStorage.getItem('has_password') === 'true',
  };
}

function persistUser(user) {
  const values = {
    token: user.token, role: user.role, username: user.username,
    user_id: user.userId, family_id: user.familyId,
    invite_code: user.inviteCode, family_name: user.familyName,
    has_password: user.hasPassword,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value == null || value === '') sessionStorage.removeItem(key);
    else sessionStorage.setItem(key, String(value));
  });
}

export default function useAuth() {
  const [googleRegistrationToken, setGoogleRegistrationToken] = useState(null);
  const [oauthError, setOauthError] = useState('');
  const [user, setUser] = useState(readStoredUser);
  const [familyMembers, setFamilyMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    sessionStorage.clear();
    setUser(emptyUser);
    setFamilyMembers([]);
  }, []);

  const loadFamilyInformation = useCallback(async (familyId) => {
    if (!familyId) return { inviteCode: '', familyName: '' };
    const families = await getFamilies();
    const family = (Array.isArray(families) ? families : []).find(
      (entry) => String(entry.id) === String(familyId)
    );
    return {
      inviteCode: family?.invite_code || '',
      familyName: family?.name || '',
    };
  }, []);

  const loadFamilyMembers = useCallback(async () => {
    try {
      const members = await getUsers();
      setFamilyMembers(Array.isArray(members) ? members : []);
    } catch (error) {
      console.error('Не вдалося завантажити учасників родини:', error);
      if (/401|не авториз/i.test(error.message)) logout();
    }
  }, [logout]);

  const hydrateSession = useCallback(async (token) => {
    sessionStorage.setItem('token', token);
    const data = await getCurrentUser();
    const familyInfo = data.role === 'admin'
      ? { inviteCode: '', familyName: '' }
      : await loadFamilyInformation(data.family_id);
    const nextUser = {
      token,
      role: data.role,
      username: data.username,
      userId: data.id,
      familyId: data.family_id || '',
      inviteCode: data.family_invite_code || familyInfo.inviteCode,
      familyName: familyInfo.familyName,
      hasPassword: data.has_password ?? false,
    };
    persistUser(nextUser);
    setUser(nextUser);
    return nextUser;
  }, [loadFamilyInformation]);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const params = new URLSearchParams(
          window.location.hash.replace(/^#/, '')
        );

        const oauthToken = params.get('access_token');
        const registrationToken = params.get('google_registration_token');
        const oauthErrorParam = params.get('oauth_error');
        const googleLinked = params.get('google_linked');

        if (
          oauthToken ||
          registrationToken ||
          oauthErrorParam ||
          googleLinked
        ) {
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname
          );
        }

        if (oauthToken) {
          await hydrateSession(oauthToken);
        } else if (registrationToken) {
          setGoogleRegistrationToken(registrationToken);
        } else if (oauthErrorParam === 'account_exists') {
          setOauthError(
            'Акаунт із таким email уже існує. Увійдіть за допомогою пароля, а потім прив’яжіть Google у профілі.'
          );
        }

        if (
          !oauthToken &&
          !registrationToken &&
          !oauthErrorParam &&
          user.token
        ) {
          await hydrateSession(user.token);
        }
      } catch (error) {
        console.error('Не вдалося відновити сесію:', error);
        if (!cancelled) logout();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (user.token && user.role !== 'admin') loadFamilyMembers();
    else setFamilyMembers([]);
  }, [user.token, user.role, loadFamilyMembers]);

  const login = async (credentials) => {
    const data = await loginUser(credentials);
    return hydrateSession(data.access_token);
  };

  const register = async (formData) => {
    const createFamilyFlag = Boolean(formData.create_family ?? formData.createFamily);

    const familyName = formData.family_name ?? formData.familyName ?? '';
    const inviteCode = formData.invite_code ?? formData.inviteCode ?? '';

    if (createFamilyFlag && !familyName.trim()) {
      throw new Error('Введіть назву родини.');
    }

    if (!createFamilyFlag && !inviteCode.trim()) {
      throw new Error('Введіть код запрошення родини.');
    }

    return await registerUser({
      username: formData.username.trim(),
      email: formData.email.trim(),
      password: formData.password,
      invite_code: createFamilyFlag ? null : inviteCode.trim(),
      family_name: createFamilyFlag ? familyName.trim() : null,
      create_family: createFamilyFlag,
    });
  };

  const finishGoogleRegistration = async (formData) => {
    if (!googleRegistrationToken) {
      throw new Error('Сесія Google-реєстрації втрачена. Спробуйте ще раз.');
    }

    const data = await completeGoogleRegistration({
      registration_token: googleRegistrationToken,
      password: formData.password,
      username: formData.username || undefined,
      create_family: formData.create_family,
      family_name: formData.create_family
        ? formData.family_name.trim()
        : null,
      invite_code: formData.create_family
        ? null
        : formData.invite_code.trim(),
    });

    setGoogleRegistrationToken(null);
    await hydrateSession(data.access_token);
  };

  const linkGoogle = async () => {
    if (!user.token) {
      throw new Error('Спочатку увійдіть у FamilyPlan.');
    }

    const result = await createGoogleLinkToken(user.token);

    window.location.assign(
      getGoogleLinkUrl(result.link_token)
    );
  };

  const changeMemberRole = async (member, newRole, isMe = false) => {
    const result = await updateUser(member.id, { role: newRole });
    if (isMe) await hydrateSession(result.access_token || user.token);
    await loadFamilyMembers();
  };

  const removeMember = async (member) => {
    await deleteUser(member.id);
    await loadFamilyMembers();
  };

  const addFamilyMember = async (data) => {
    if (!user.inviteCode) throw new Error('Не знайдено код запрошення родини.');
    await registerUser({
      username: data.username,
      email: data.email,
      password: data.password,
      invite_code: user.inviteCode,
    });
    await loadFamilyMembers();
  };

  const renameFamily = async (familyName) => {
    if (!user.familyId) throw new Error('Користувач не належить до родини.');
    const updated = await updateFamily(user.familyId, { name: familyName });
    const next = { ...user, familyName: updated.name };
    persistUser(next);
    setUser(next);
  };

  const updateUsername = async (username) => {
    const result = await updateUser(user.userId, { username });
    const next = { ...user, username: result.username || username, token: result.access_token || user.token };
    persistUser(next);
    setUser(next);
    if (result.access_token) sessionStorage.setItem('token', result.access_token);
  };
  const deleteMyAccount = async () => {
    await deleteUser(user.userId);
    logout();
  };
  const removeFamily = async () => {
    if (!user.familyId) {
      throw new Error('Користувач не належить до родини.');
    }

    await deleteFamily(user.familyId);
    logout();
  };

  return {
    user, familyMembers, loading, login, register, logout,
    loadFamilyMembers, changeMemberRole, removeMember,
    addFamilyMember, updateUsername, renameFamily, deleteMyAccount,
    removeFamily, googleRegistrationToken, oauthError,
    finishGoogleRegistration, linkGoogle,
  };
}