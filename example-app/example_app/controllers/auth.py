from mountaineer_auth import LoginController as AuthLoginController


class LoginController(AuthLoginController):
    view_path = "/app/auth/login/page.tsx"
