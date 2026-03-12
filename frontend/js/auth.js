class AuthService {
    static TOKEN_KEY = 'securework_access';
    static REFRESH_KEY = 'securework_refresh';
    static ROLE_KEY = 'securework_role';
    static USERNAME_KEY = 'securework_username';
    static API_BASE = 'https://securework-api.onrender.com';

    // Helper to decode JWT and get the custom role
    static decodeJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(window.atob(base64));
        } catch (e) {
            return null;
        }
    }

    static async login(email, password) {
        try {
            // Django expects 'username' by default, so we map the email field to it
            const response = await fetch(`${this.API_BASE}/token/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email, password: password }),
            });

            if (!response.ok) return { success: false, error: 'Invalid credentials' };

            const data = await response.json();
            
            // Store SimpleJWT tokens
            localStorage.setItem(this.TOKEN_KEY, data.access);
            localStorage.setItem(this.REFRESH_KEY, data.refresh);
            //temporary email store karenge abhi, aage jaake isko user model se first name and last name ko map karenge
            localStorage.setItem(this.USERNAME_KEY, email);

            // Decode token to find if they are Client or Freelancer
            const payload = this.decodeJWT(data.access);
            if (payload) {
                if (payload.role) localStorage.setItem(this.ROLE_KEY, payload.role);

                if (payload.first_name || payload.last_name) {
                    const fullName = `${payload.first_name || ''} ${payload.last_name || ''}`.trim();
                    localStorage.setItem(this.USERNAME_KEY, fullName)
                }
            }

            return { success: true };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Server connection failed.' };
        }
    }

    // static getUser(){
    //     if (!this.isAuthenticated()) return null;
    //     return {
    //         name: localStorage.getItem(this.USERNAME_KEY) || 'User',
    //         role: localStorage.getItem(this.ROLE_KEY) || 'client'
            
    //     };
    // }

    static async register(email, password, fullName, role, company) {
        try {
            const nameParts = fullName.trim().split(' ');
            const firstName = nameParts[0] || '';
            const lastName = nameParts.slice(1).join(' ') || '';

            const response = await fetch(`${this.API_BASE}/api/register/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: email, // Mapping email to username
                    email: email, 
                    password: password,
                    role: role,
                    first_name: firstName, 
                    last_name: lastName, 
                    company: company
                }),
            });

            if (!response.ok) {
                const errData = await response.json();
                return { success: false, error: JSON.stringify(errData) };
            }

            // After successful registration, automatically log them in
            return await this.login(email, password);
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, error: 'Server connection failed.' };
        }
    }

    static logout() {
        localStorage.clear(); // Clears all SecureWork data safely
        window.location.href = 'login.html';
    }

    static isAuthenticated() {
        return !!localStorage.getItem(this.TOKEN_KEY);
    }

    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static getUser() {
        // Construct a pseudo-user object for the UI since DRF just sends tokens
        if (!this.isAuthenticated()) return null;
        return {
            name: localStorage.getItem(this.USERNAME_KEY) || 'User',
            role: localStorage.getItem(this.ROLE_KEY) || 'client'
        };
    }

}

