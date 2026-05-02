import apiClient from './apiClient';

const getErrorMessage = (error, fallbackMessage) => {
	const data = error?.response?.data;

	if (typeof data === 'string') return data;
	if (data?.detail) return data.detail;
	if (data?.message) return data.message;
	if (Array.isArray(data?.errors) && data.errors.length > 0) {
		return data.errors[0]?.message || fallbackMessage;
	}

	return error?.message || fallbackMessage;
};

const extractAccessToken = (data) =>
	data?.tokens?.access || data?.access_token || data?.token || data?.jwt || null;

const extractRefreshToken = (data) => data?.tokens?.refresh || data?.refresh_token || null;

const persistAuthResponse = (data, fallbackUser = {}, authProvider = 'password') => {
	const token = extractAccessToken(data);
	const refreshToken = extractRefreshToken(data);

	if (!token) {
		throw new Error('Login succeeded but no token was returned by the server.');
	}

	localStorage.setItem('authToken', token);

	if (refreshToken) {
		localStorage.setItem('refreshToken', refreshToken);
	}

	localStorage.setItem('user', JSON.stringify({
		...(data?.user || fallbackUser),
		authProvider,
	}));
};

const AuthService = {
	async login(username, password) {
		try {
			const response = await apiClient.post('/auth/login', { username, password });
			persistAuthResponse(response.data, { username }, 'password');

			return response.data;
		} catch (error) {
			throw new Error(getErrorMessage(error, 'Invalid credentials. Please try again.'));
		}
	},

	async register(formData) {
		try {
			const payload = {
				username: formData.username,
				email: formData.email,
				password: formData.password,
				location: formData.locationType === 'Inside Beirut',
			};

			const response = await apiClient.post('/auth/register', payload);
			return response.data;
		} catch (error) {
			throw new Error(getErrorMessage(error, 'Registration failed. Please try again.'));
		}
	},

	async googleLogin(idToken) {
		try {
			const response = await apiClient.post('/auth/google', {
				id_token: idToken,
			});

			persistAuthResponse(response.data, {}, 'google');
			return response.data;
		} catch (error) {
			throw new Error(getErrorMessage(error, 'Google login failed. Please try again.'));
		}
	},

	async logout() {
		let apiLogoutSucceeded = false;
		const refreshToken = this.getRefreshToken();

		try {
			if (refreshToken) {
				await apiClient.post('/auth/logout', { refresh: refreshToken });
				apiLogoutSucceeded = true;
			}
		} catch (_error) {
			apiLogoutSucceeded = false;
		} finally {
			localStorage.removeItem('authToken');
			localStorage.removeItem('refreshToken');
			localStorage.removeItem('user');
		}

		return apiLogoutSucceeded;
	},

	async updateLocation(location) {
		try {
			const response = await apiClient.patch('/auth/location', { location });
			const storedUser = this.getUser() || {};
			const updatedUser = {
				...storedUser,
				location: response.data?.location ?? location,
			};

			localStorage.setItem('user', JSON.stringify(updatedUser));
			return response.data;
		} catch (error) {
			throw new Error(getErrorMessage(error, 'Failed to update location. Please try again.'));
		}
	},

	async changePassword(oldPassword, newPassword) {
		try {
			const response = await apiClient.post('/auth/password', {
				old_password: oldPassword,
				new_password: newPassword,
			});

			return response.data;
		} catch (error) {
			throw new Error(getErrorMessage(error, 'Failed to change password. Please try again.'));
		}
	},

	isAuthenticated() {
		return !!localStorage.getItem('authToken');
	},

	getUser() {
		const user = localStorage.getItem('user');
		return user ? JSON.parse(user) : null;
	},

	getToken() {
		return localStorage.getItem('authToken');
	},

	getRefreshToken() {
		return localStorage.getItem('refreshToken');
	},
};

export default AuthService;
