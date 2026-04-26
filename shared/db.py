<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <meta name="description" content="I Hub - Système de gestion hospitalière">
    <meta name="theme-color" content="#0a5c7e">
    <title>I Hub</title>

    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js"></script>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="logo.jpg">
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <img src="logo.jpg" alt="I Hub" class="loading-logo">
            <div class="loading-pulse"></div>
        </div>
    </div>

    <div class="toast-container" id="toastContainer"></div>

    <button class="mobile-menu-btn" id="mobileMenuBtn" onclick="toggleSidebar()" aria-label="Ouvrir le menu">
        <i class="fas fa-bars"></i>
    </button>

    <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>

    <div class="auth-container" id="authContainer">
        <div class="auth-split">
            <section class="auth-branding" aria-label="Présentation de l'hôpital">
                <div class="branding-content">
                    <div class="branding-logo-block">
                        <img src="logo.jpg" alt="Logo de l'hôpital" class="brand-logo-img">
                        <div class="branding-copy">
                            <p class="branding-kicker">I Hub</p>
                            <h1 class="branding-title">Gestion hospitalière centralisée</h1>
                            <p class="branding-text">
                                Admissions, prescriptions, laboratoire, pharmacie et facturation dans un seul espace.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="branding-footer">
                    <p class="branding-hospital-name">Hôpital I Hub</p>
                </div>
            </section>

            <section class="auth-form-container" aria-label="Authentification">
                <div class="auth-card">
                    <div class="auth-header">
                        <div class="auth-logo-mobile">
                            <img src="logo.jpg" alt="I Hub" class="mobile-logo-img">
                        </div>
                        <h2 class="auth-title" id="appName">I Hub</h2>
                        <p class="auth-subtitle">Hospital Management System</p>
                        <p class="auth-welcome">Bienvenue dans votre espace de travail sécurisé</p>
                    </div>

                    <div class="tab-buttons">
                        <button class="tab-btn active" type="button" onclick="switchTab('login')">Connexion</button>
                        <button class="tab-btn" type="button" onclick="switchTab('register')">Inscription</button>
                    </div>

                    <form id="loginForm" onsubmit="handleLogin(event)">
                        <div class="form-group">
                            <label class="form-label" for="loginEmail">Email professionnel</label>
                            <input type="email" class="form-control" id="loginEmail" required placeholder="nom@ushuda.com" autocomplete="username">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="loginPassword">Mot de passe</label>
                            <input type="password" class="form-control" id="loginPassword" required placeholder="••••••••" autocomplete="current-password">
                        </div>
                        <label class="remember-row">
                            <input type="checkbox" id="rememberMe">
                            <span>Rester connecté sur cet appareil</span>
                        </label>
                        <button type="submit" class="btn btn-primary btn-full">
                            <i class="fas fa-arrow-right"></i> Se connecter
                        </button>
                    </form>

                    <form id="registerForm" onsubmit="handleRegister(event)" style="display: none;">
                        <div class="form-group">
                            <label class="form-label" for="registerName">Nom complet</label>
                            <input type="text" class="form-control" id="registerName" required autocomplete="name">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="registerEmail">Email professionnel</label>
                            <input type="email" class="form-control" id="registerEmail" required placeholder="prenom.nom@ushuda.com" autocomplete="email">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="registerPassword">Mot de passe</label>
                            <input type="password" class="form-control" id="registerPassword" required minlength="8" autocomplete="new-password">
                            <small class="field-hint">Minimum 8 caractères</small>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="registerRole">Rôle</label>
                            <select class="form-control" id="registerRole">
                                <option value="docteur">Médecin</option>
                                <option value="infirmier">Infirmier</option>
                                <option value="laboratoire">Laboratoire</option>
                                <option value="pharmacie">Pharmacie</option>
                                <option value="reception">Réception</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary btn-full">
                            <i class="fas fa-user-plus"></i> Créer mon compte
                        </button>
                    </form>

                    <div class="auth-footer">
                        <p><i class="fas fa-shield-alt"></i> Système sécurisé pour les opérations médicales</p>
                    </div>
                </div>
            </section>
        </div>
    </div>

    <div class="dashboard" id="dashboard">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-logo">
                    <img src="logo.jpg" alt="I Hub" class="sidebar-logo-img">
                    <h2><span id="sidebarAppName">I Hub</span></h2>
                </div>
                <p id="userInfo">Chargement...</p>
            </div>
            <div class="nav-menu" id="navMenu"></div>
            <div class="sidebar-footer">
                <button class="btn btn-danger btn-sm btn-full" onclick="logout()">
                    <i class="fas fa-sign-out-alt"></i> Déconnexion
                </button>
            </div>
        </div>

        <main class="main-content" id="mainContent"></main>
    </div>

    <script src="app.js" defer></script>
</body>
</html>
