var Auth = {
    isLoggedIn: false,
    username: null,

    init: async function() {
        try {
            var res = await fetch('/api/auth/me', { credentials: 'include' });
            if (res.ok) {
                var data = await res.json();
                this.isLoggedIn = true;
                this.username = data.username;
                this.showApp();
            } else {
                this.showLogin();
            }
        } catch (err) {
            this.showLogin();
        }
    },

    showLogin: function() {
        document.getElementById('loginScreen').classList.add('active');
        document.getElementById('appScreen').classList.remove('active');
    },

    showApp: function() {
        document.getElementById('loginScreen').classList.remove('active');
        document.getElementById('appScreen').classList.add('active');
        document.getElementById('usernameDisplay').textContent = this.username;
        App.init();
    },

    login: async function() {
        var username = document.getElementById('loginUsername').value.trim();
        var password = document.getElementById('loginPassword').value;
        var errorEl = document.getElementById('loginError');

        if (!username || !password) {
            errorEl.textContent = 'Please enter username and password';
            return;
        }

        try {
            var res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username: username, password: password })
            });
            var data = await res.json();
            if (res.ok) {
                this.isLoggedIn = true;
                this.username = data.username;
                this.showApp();
            } else {
                errorEl.textContent = data.error || 'Login failed';
            }
        } catch (err) {
            console.error('Login error:', err);
            errorEl.textContent = 'Connection error - is the server running?';
        }
    },

    register: async function() {
        var username = document.getElementById('loginUsername').value.trim();
        var password = document.getElementById('loginPassword').value;
        var errorEl = document.getElementById('loginError');

        if (!username || !password) {
            errorEl.textContent = 'Please enter username and password';
            return;
        }
        if (password.length < 6) {
            errorEl.textContent = 'Password must be at least 6 characters';
            return;
        }

        try {
            var res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username: username, password: password })
            });
            var data = await res.json();
            if (res.ok) {
                this.isLoggedIn = true;
                this.username = data.username;
                this.showApp();
            } else {
                errorEl.textContent = data.error || 'Registration failed';
            }
        } catch (err) {
            errorEl.textContent = 'Connection error';
        }
    },

    logout: async function() {
        try {
            await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
        } catch (err) {}
        this.isLoggedIn = false;
        this.username = null;
        this.showLogin();
    }
};
