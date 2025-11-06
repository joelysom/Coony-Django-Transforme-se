const wrapper = document.querySelector('.wrapper')
const registerLink = document.querySelector('.register-link')
const loginLink = document.querySelector('.login-link')
const langSelect = document.getElementById('langSelect')
const footerDesc = document.getElementById('footer-desc')
const brandText = document.querySelector('.brand-text')
const wrapperTexts = {
    loginTitle: document.querySelector('.form-box.login .title'),
    loginUserLabel: document.querySelector('.form-box.login .input-box:nth-child(1) label'),
    loginPassLabel: document.querySelector('.form-box.login .input-box:nth-child(2) label'),
    loginButton: document.querySelector('.form-box.login button'),
    loginLinkText: document.querySelector('.form-box.login .linkTxt p'),
    registerTitle: document.querySelector('.form-box.register .title'),
    registerUserLabel: document.querySelector('.form-box.register .input-box:nth-child(1) label'),
    registerEmailLabel: document.querySelector('.form-box.register .input-box:nth-child(2) label'),
    registerPassLabel: document.querySelector('.form-box.register .input-box:nth-child(3) label'),
    registerButton: document.querySelector('.form-box.register button'),
    registerLinkText: document.querySelector('.form-box.register .linkTxt p'),
    infoLoginTitle: document.querySelector('.info-text.login h2'),
    infoLoginDesc: document.querySelector('.info-text.login p'),
    infoRegisterTitle: document.querySelector('.info-text.register h2'),
    infoRegisterDesc: document.querySelector('.info-text.register p')
}

const translations = {
    pt: {
        footer: 'Plataforma que conecta pessoas e permite indicações com reconhecimento.',
        brand: 'O Saúde em Movimento (Conny) é mais do que um app, é um convite.\nCriado para quem quer começar, recomeçar ou simplesmente se sentir bem, o aplicativo conecta pessoas a atividades físicas, eventos esportivos e experiências reais.',
        loginTitle: 'Entrar',
        loginUserLabel: 'Usuário',
        loginPassLabel: 'Senha',
        loginButton: 'Entrar',
        loginLinkText: 'Não tem uma conta? <a href="#" class="register-link">Cadastre-se</a>',
        registerTitle: 'Cadastre-se',
        registerUserLabel: 'Usuário',
        registerEmailLabel: 'E-mail',
        registerPassLabel: 'Senha',
        registerButton: 'Cadastrar',
        registerLinkText: 'Já tem uma conta? <a href="#" class="login-link">Entrar</a>',
        infoLoginTitle: 'Bem-vindo de volta!',
        infoLoginDesc: 'Insira seus dados cadastrados para acessar o programa.',
        infoRegisterTitle: 'Bem-vindo!',
        infoRegisterDesc: 'Insira seus dados para criar uma nova conta.'
    },
    en: {
        footer: 'Platform that connects people and enables referrals with recognition.',
        brand: 'Saúde em Movimento (Conny) is more than an app, it is an invitation.\nCreated for those who want to start, restart, or simply feel good, the application connects people to physical activities, sports events, and real experiences.',
        loginTitle: 'Login',
        loginUserLabel: 'Username',
        loginPassLabel: 'Password',
        loginButton: 'Login',
        loginLinkText: 'Don\'t have an account? <a href="#" class="register-link">Sign up</a>',
        registerTitle: 'Sign up',
        registerUserLabel: 'Username',
        registerEmailLabel: 'Email',
        registerPassLabel: 'Password',
        registerButton: 'Sign up',
        registerLinkText: 'Already have an account? <a href="#" class="login-link">Login</a>',
        infoLoginTitle: 'Welcome back!',
        infoLoginDesc: 'Enter your registered details to access the program.',
        infoRegisterTitle: 'Welcome!',
        infoRegisterDesc: 'Enter your details to create a new account.'
    },
    jp: {
        footer: '人々をつなぎ、推薦による報酬を可能にするプラットフォーム。',
        brand: 'Saúde em Movimento（Conny）は単なるアプリではなく、招待状です。\n始めたい方、再スタートしたい方、ただ気分を良くしたい方のために作られたこのアプリは、人々をフィットネス、スポーツイベント、リアルな体験へとつなげます。',
        loginTitle: 'ログイン',
        loginUserLabel: 'ユーザー名',
        loginPassLabel: 'パスワード',
        loginButton: 'ログイン',
        loginLinkText: 'アカウントをお持ちでないですか？ <a href="#" class="register-link">サインアップ</a>',
        registerTitle: 'サインアップ',
        registerUserLabel: 'ユーザー名',
        registerEmailLabel: 'メール',
        registerPassLabel: 'パスワード',
        registerButton: 'サインアップ',
        registerLinkText: 'すでにアカウントをお持ちですか？ <a href="#" class="login-link">ログイン</a>',
        infoLoginTitle: 'お帰りなさい！',
        infoLoginDesc: '登録済みの詳細を入力してプログラムにアクセスしてください。',
        infoRegisterTitle: 'ようこそ！',
        infoRegisterDesc: '新しいアカウントを作成するための詳細を入力してください。'
    },
    kr: {
        footer: '사람들을 연결하고 추천으로 보상을 얻을 수 있는 플랫폼입니다.',
        brand: 'Saúde em Movimento(Conny)는 단순한 앱이 아니라 초대입니다.\n시작하고 싶거나, 다시 시작하고 싶거나, 단순히 기분이 좋아지고 싶은 사람들을 위해 만들어진 이 앱은 사람들을 신체 활동, 스포츠 이벤트 및 실제 경험에 연결합니다.',
        loginTitle: '로그인',
        loginUserLabel: '사용자 이름',
        loginPassLabel: '비밀번호',
        loginButton: '로그인',
        loginLinkText: '계정이 없으신가요? <a href="#" class="register-link">가입하기</a>',
        registerTitle: '가입하기',
        registerUserLabel: '사용자 이름',
        registerEmailLabel: '이메일',
        registerPassLabel: '비밀번호',
        registerButton: '가입하기',
        registerLinkText: '이미 계정이 있으신가요? <a href="#" class="login-link">로그인</a>',
        infoLoginTitle: '다시 오신 것을 환영합니다!',
        infoLoginDesc: '등록된 세부 정보를 입력하여 프로그램에 액세스하세요.',
        infoRegisterTitle: '환영합니다!',
        infoRegisterDesc: '새 계정을 만들기 위한 세부 정보를 입력하세요.'
    }
}

const reassignLinkEvents = () => {
    const registerLink = document.querySelector('.register-link');
    const loginLink = document.querySelector('.login-link');

    registerLink.onclick = () => {
        wrapper.classList.add('active');
    };

    loginLink.onclick = () => {
        wrapper.classList.remove('active');
    };
};

if (langSelect && footerDesc && brandText) {
    langSelect.addEventListener('change', (e) => {
        const v = e.target.value;
        const t = translations[v] || translations.pt;
        footerDesc.textContent = t.footer;
        brandText.textContent = t.brand;
        wrapperTexts.loginTitle.textContent = t.loginTitle;
        wrapperTexts.loginUserLabel.textContent = t.loginUserLabel;
        wrapperTexts.loginPassLabel.textContent = t.loginPassLabel;
        wrapperTexts.loginButton.textContent = t.loginButton;
        wrapperTexts.loginLinkText.innerHTML = t.loginLinkText;
        wrapperTexts.registerTitle.textContent = t.registerTitle;
        wrapperTexts.registerUserLabel.textContent = t.registerUserLabel;
        wrapperTexts.registerEmailLabel.textContent = t.registerEmailLabel;
        wrapperTexts.registerPassLabel.textContent = t.registerPassLabel;
        wrapperTexts.registerButton.textContent = t.registerButton;
        wrapperTexts.registerLinkText.innerHTML = t.registerLinkText;
        wrapperTexts.infoLoginTitle.textContent = t.infoLoginTitle;
        wrapperTexts.infoLoginDesc.textContent = t.infoLoginDesc;
        wrapperTexts.infoRegisterTitle.textContent = t.infoRegisterTitle;
        wrapperTexts.infoRegisterDesc.textContent = t.infoRegisterDesc;

        reassignLinkEvents();
    });
}

reassignLinkEvents();

const loginForm = document.querySelector('.form-box.login form');

if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevent default form submission

        const usernameInput = loginForm.querySelector('input[type="text"]');
        const passwordInput = loginForm.querySelector('input[type="password"]');

        if (usernameInput.value === 'teste' && passwordInput.value === 'teste') {
            window.location.href = '/pages/home/home.html'; // Redirect to correct home path
        } else {
            alert('Usuário ou senha incorretos!');
        }
    });
}