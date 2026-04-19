"""
i18n.py — SpeakAgain v2.1 UI translations
------------------------------------------
Every piece of interface text is defined here in all 9 supported languages.
Previous versions translated only phrases; the app chrome stayed English.
v2.1 translates everything: menus, buttons, headings, placeholders, help text.

Usage:
    from i18n import t
    t("nav.communication", "English")  -> "Communication"
    t("nav.communication", "Spanish")  -> "Comunicación"

Missing translations fall back to English.
"""

# Translation dictionary. Keys are dot-separated namespaces.
TRANSLATIONS = {
    # ========== NAVIGATION ==========
    "nav.communication": {
        "English": "Communication", "Spanish": "Comunicación", "French": "Communication",
        "Portuguese": "Comunicação", "Arabic": "التواصل",
        "Yoruba": "Ibanisọrọ", "Igbo": "Nkwurịta okwu", "Hausa": "Sadarwa", "Pidgin": "Talk Talk",
    },
    "nav.exercises": {
        "English": "Exercises", "Spanish": "Ejercicios", "French": "Exercices",
        "Portuguese": "Exercícios", "Arabic": "التمارين",
        "Yoruba": "Awọn idaraya", "Igbo": "Mmega ahụ", "Hausa": "Motsa jiki", "Pidgin": "Exercises",
    },
    "nav.games": {
        "English": "Games", "Spanish": "Juegos", "French": "Jeux",
        "Portuguese": "Jogos", "Arabic": "الألعاب",
        "Yoruba": "Awọn ere", "Igbo": "Egwuregwu", "Hausa": "Wasanni", "Pidgin": "Games",
    },
    "nav.progress": {
        "English": "Progress", "Spanish": "Progreso", "French": "Progrès",
        "Portuguese": "Progresso", "Arabic": "التقدم",
        "Yoruba": "Ilọsiwaju", "Igbo": "Ọganihu", "Hausa": "Ci gaba", "Pidgin": "Progress",
    },
    "nav.family": {
        "English": "Family", "Spanish": "Familia", "French": "Famille",
        "Portuguese": "Família", "Arabic": "العائلة",
        "Yoruba": "Ẹbi", "Igbo": "Ezinụlọ", "Hausa": "Iyali", "Pidgin": "Family",
    },
    "nav.caregiver": {
        "English": "Caregiver", "Spanish": "Cuidador", "French": "Soignant",
        "Portuguese": "Cuidador", "Arabic": "مقدم الرعاية",
        "Yoruba": "Oluranlowo", "Igbo": "Onye na-elekọta", "Hausa": "Mai kulawa", "Pidgin": "Caregiver",
    },
    "nav.settings": {
        "English": "Settings", "Spanish": "Configuración", "French": "Paramètres",
        "Portuguese": "Configurações", "Arabic": "الإعدادات",
        "Yoruba": "Eto", "Igbo": "Ntọala", "Hausa": "Saituna", "Pidgin": "Settings",
    },
    "nav.dashboard": {
        "English": "Family dashboard", "Spanish": "Panel familiar", "French": "Tableau familial",
        "Portuguese": "Painel da família", "Arabic": "لوحة العائلة",
        "Yoruba": "Igbimọ ẹbi", "Igbo": "Dashboard ezinụlọ", "Hausa": "Dashboard na iyali", "Pidgin": "Family Dashboard",
    },
    "nav.logout": {
        "English": "Log out", "Spanish": "Cerrar sesión", "French": "Déconnexion",
        "Portuguese": "Sair", "Arabic": "تسجيل الخروج",
        "Yoruba": "Jade", "Igbo": "Pụọ", "Hausa": "Fita", "Pidgin": "Log out",
    },

    # ========== GENERIC BUTTONS ==========
    "btn.save": {
        "English": "Save", "Spanish": "Guardar", "French": "Enregistrer",
        "Portuguese": "Salvar", "Arabic": "حفظ",
        "Yoruba": "Fipamọ", "Igbo": "Chekwaa", "Hausa": "Ajiye", "Pidgin": "Save",
    },
    "btn.cancel": {
        "English": "Cancel", "Spanish": "Cancelar", "French": "Annuler",
        "Portuguese": "Cancelar", "Arabic": "إلغاء",
        "Yoruba": "Fagilee", "Igbo": "Kagbuo", "Hausa": "Soke", "Pidgin": "Cancel",
    },
    "btn.continue": {
        "English": "Continue", "Spanish": "Continuar", "French": "Continuer",
        "Portuguese": "Continuar", "Arabic": "متابعة",
        "Yoruba": "Tẹsiwaju", "Igbo": "Gaa n'ihu", "Hausa": "Ci gaba", "Pidgin": "Continue",
    },
    "btn.next": {
        "English": "Next", "Spanish": "Siguiente", "French": "Suivant",
        "Portuguese": "Próximo", "Arabic": "التالي",
        "Yoruba": "Tókàn", "Igbo": "Ọzọ", "Hausa": "Na gaba", "Pidgin": "Next",
    },
    "btn.check": {
        "English": "Check", "Spanish": "Verificar", "French": "Vérifier",
        "Portuguese": "Verificar", "Arabic": "تحقق",
        "Yoruba": "Ṣayẹwo", "Igbo": "Lelee", "Hausa": "Duba", "Pidgin": "Check",
    },
    "btn.speak": {
        "English": "Speak", "Spanish": "Hablar", "French": "Parler",
        "Portuguese": "Falar", "Arabic": "تحدث",
        "Yoruba": "Sọ", "Igbo": "Kwuo", "Hausa": "Yi magana", "Pidgin": "Talk",
    },
    "btn.hint": {
        "English": "Hint", "Spanish": "Pista", "French": "Indice",
        "Portuguese": "Dica", "Arabic": "تلميح",
        "Yoruba": "Ìmọ̀ràn", "Igbo": "Ntụaka", "Hausa": "Alama", "Pidgin": "Hint",
    },
    "btn.submit": {
        "English": "Submit", "Spanish": "Enviar", "French": "Soumettre",
        "Portuguese": "Enviar", "Arabic": "إرسال",
        "Yoruba": "Firanṣẹ", "Igbo": "Zipu", "Hausa": "Aika", "Pidgin": "Submit",
    },
    "btn.play": {
        "English": "Play", "Spanish": "Jugar", "French": "Jouer",
        "Portuguese": "Jogar", "Arabic": "العب",
        "Yoruba": "Ṣere", "Igbo": "Gwuo egwu", "Hausa": "Yi wasa", "Pidgin": "Play",
    },
    "btn.remove": {
        "English": "Remove", "Spanish": "Eliminar", "French": "Supprimer",
        "Portuguese": "Remover", "Arabic": "إزالة",
        "Yoruba": "Yọkuro", "Igbo": "Wepụ", "Hausa": "Cire", "Pidgin": "Remove",
    },
    "btn.add": {
        "English": "Add", "Spanish": "Añadir", "French": "Ajouter",
        "Portuguese": "Adicionar", "Arabic": "إضافة",
        "Yoruba": "Fikun", "Igbo": "Tinye", "Hausa": "Ƙara", "Pidgin": "Add",
    },
    "btn.close": {
        "English": "Close", "Spanish": "Cerrar", "French": "Fermer",
        "Portuguese": "Fechar", "Arabic": "إغلاق",
        "Yoruba": "Pa", "Igbo": "Mechie", "Hausa": "Rufe", "Pidgin": "Close",
    },

    # ========== AUTH ==========
    "auth.welcome_title": {
        "English": "Welcome to SpeakAgain", "Spanish": "Bienvenido a SpeakAgain",
        "French": "Bienvenue sur SpeakAgain", "Portuguese": "Bem-vindo ao SpeakAgain",
        "Arabic": "مرحبا بكم في SpeakAgain", "Yoruba": "Kaabọ si SpeakAgain",
        "Igbo": "Nnọọ na SpeakAgain", "Hausa": "Barka da zuwa SpeakAgain", "Pidgin": "Welcome to SpeakAgain",
    },
    "auth.login": {
        "English": "Log in", "Spanish": "Iniciar sesión", "French": "Se connecter",
        "Portuguese": "Entrar", "Arabic": "تسجيل الدخول",
        "Yoruba": "Wọle", "Igbo": "Banye", "Hausa": "Shiga", "Pidgin": "Log in",
    },
    "auth.signup": {
        "English": "Sign up", "Spanish": "Registrarse", "French": "S'inscrire",
        "Portuguese": "Cadastrar", "Arabic": "التسجيل",
        "Yoruba": "Forukọsilẹ", "Igbo": "Debanye aha", "Hausa": "Yi rajista", "Pidgin": "Sign up",
    },
    "auth.username": {
        "English": "Username", "Spanish": "Nombre de usuario", "French": "Nom d'utilisateur",
        "Portuguese": "Nome de usuário", "Arabic": "اسم المستخدم",
        "Yoruba": "Orukọ olumulo", "Igbo": "Aha onye ọrụ", "Hausa": "Sunan mai amfani", "Pidgin": "Username",
    },
    "auth.password": {
        "English": "Password", "Spanish": "Contraseña", "French": "Mot de passe",
        "Portuguese": "Senha", "Arabic": "كلمة المرور",
        "Yoruba": "Ọrọ igbaniwọle", "Igbo": "Okwuntughe", "Hausa": "Kalmar wucewa", "Pidgin": "Password",
    },
    "auth.email": {
        "English": "Email", "Spanish": "Correo electrónico", "French": "Email",
        "Portuguese": "Email", "Arabic": "البريد الإلكتروني",
        "Yoruba": "Imeeli", "Igbo": "Email", "Hausa": "Imel", "Pidgin": "Email",
    },
    "auth.google": {
        "English": "Continue with Google", "Spanish": "Continuar con Google",
        "French": "Continuer avec Google", "Portuguese": "Continuar com Google",
        "Arabic": "المتابعة مع جوجل", "Yoruba": "Tẹsiwaju pẹlu Google",
        "Igbo": "Gaa n'ihu na Google", "Hausa": "Ci gaba da Google", "Pidgin": "Use Google",
    },
    "auth.or": {
        "English": "or", "Spanish": "o", "French": "ou",
        "Portuguese": "ou", "Arabic": "أو",
        "Yoruba": "tabi", "Igbo": "ma ọ bụ", "Hausa": "ko", "Pidgin": "abi",
    },
    "auth.family_invite": {
        "English": "I'm family — I have an invite code", "Spanish": "Soy familia — tengo un código de invitación",
        "French": "Je suis famille — j'ai un code d'invitation", "Portuguese": "Sou família — tenho um código",
        "Arabic": "أنا عائلة — لدي رمز دعوة", "Yoruba": "Mo je ebi — mo ni koodu",
        "Igbo": "Abụ m ezinụlọ — enwere m koodu", "Hausa": "Ni iyali ne — ina da code",
        "Pidgin": "I be family — I get code",
    },
    "auth.invite_code": {
        "English": "Invite code", "Spanish": "Código de invitación", "French": "Code d'invitation",
        "Portuguese": "Código de convite", "Arabic": "رمز الدعوة",
        "Yoruba": "Koodu ipe", "Igbo": "Koodu nkpọku", "Hausa": "Lambar gayyata", "Pidgin": "Invite code",
    },
    "auth.join_family": {
        "English": "Join family dashboard", "Spanish": "Unirse al panel",
        "French": "Rejoindre le tableau", "Portuguese": "Entrar no painel",
        "Arabic": "انضم إلى اللوحة", "Yoruba": "Darapọ mọ igbimọ",
        "Igbo": "Sonye na dashboard", "Hausa": "Shiga dashboard", "Pidgin": "Join Dashboard",
    },

    # ========== ONBOARDING ==========
    "onboard.setup_profile": {
        "English": "Set up your profile", "Spanish": "Configura tu perfil",
        "French": "Configurez votre profil", "Portuguese": "Configure seu perfil",
        "Arabic": "قم بإعداد ملفك الشخصي", "Yoruba": "Ṣeto profaili rẹ",
        "Igbo": "Doo profaịlụ gị", "Hausa": "Saita bayanan ka", "Pidgin": "Setup your Profile",
    },
    "onboard.your_name": {
        "English": "Your name", "Spanish": "Tu nombre", "French": "Votre nom",
        "Portuguese": "Seu nome", "Arabic": "اسمك",
        "Yoruba": "Orukọ rẹ", "Igbo": "Aha gị", "Hausa": "Sunanka", "Pidgin": "Your name",
    },
    "onboard.language": {
        "English": "Preferred language — app will translate fully", "Spanish": "Idioma preferido — la app se traducirá",
        "French": "Langue préférée — l'app sera traduite", "Portuguese": "Idioma — o app será traduzido",
        "Arabic": "اللغة المفضلة — ستتم ترجمة التطبيق", "Yoruba": "Ede ti o fẹ — gbogbo ohun yoo wa ni ede yii",
        "Igbo": "Asụsụ ịhọrọ — ngwa ga-asụgharị", "Hausa": "Harshen da kake so", "Pidgin": "Language wey you want",
    },
    "onboard.start_app": {
        "English": "Start SpeakAgain", "Spanish": "Iniciar SpeakAgain",
        "French": "Commencer SpeakAgain", "Portuguese": "Iniciar SpeakAgain",
        "Arabic": "ابدأ SpeakAgain", "Yoruba": "Bẹrẹ SpeakAgain",
        "Igbo": "Malite SpeakAgain", "Hausa": "Fara SpeakAgain", "Pidgin": "Start SpeakAgain",
    },

    # ========== COMMUNICATION MODE ==========
    "comm.title": {
        "English": "Communication mode", "Spanish": "Modo de comunicación",
        "French": "Mode communication", "Portuguese": "Modo de comunicação",
        "Arabic": "وضع التواصل", "Yoruba": "Ipo ibanisọrọ",
        "Igbo": "Ọnọdụ nkwurịta okwu", "Hausa": "Yanayin sadarwa", "Pidgin": "Talk Mode",
    },
    "comm.prompt": {
        "English": "What do you want to say?", "Spanish": "¿Qué quieres decir?",
        "French": "Que voulez-vous dire ?", "Portuguese": "O que você quer dizer?",
        "Arabic": "ماذا تريد أن تقول؟", "Yoruba": "Kini o fẹ sọ?",
        "Igbo": "Gịnị ka ịchọrọ ikwu?", "Hausa": "Me kake son cewa?", "Pidgin": "Wetin you wan talk?",
    },
    "comm.complete": {
        "English": "Complete", "Spanish": "Completar", "French": "Compléter",
        "Portuguese": "Completar", "Arabic": "إكمال",
        "Yoruba": "Pari", "Igbo": "Mezuo", "Hausa": "Kammala", "Pidgin": "Complete",
    },
    "comm.tap_word": {
        "English": "Tap a word to hear it spoken:", "Spanish": "Toca una palabra para escucharla:",
        "French": "Appuyez sur un mot pour l'entendre :", "Portuguese": "Toque em uma palavra para ouvir:",
        "Arabic": "اضغط على الكلمة لسماعها:", "Yoruba": "Tẹ ọrọ lati gbọ:",
        "Igbo": "Pịa okwu ịnụ ya:", "Hausa": "Latsa kalma don ka ji:", "Pidgin": "Touch word make you hear am:",
    },
    "comm.family_suggestions": {
        "English": "Family suggestions based on your saved names:",
        "Spanish": "Sugerencias familiares basadas en nombres guardados:",
        "French": "Suggestions familiales basées sur les noms enregistrés :",
        "Portuguese": "Sugestões familiares com base nos nomes salvos:",
        "Arabic": "اقتراحات عائلية بناء على الأسماء المحفوظة:",
        "Yoruba": "Awọn imọran ẹbi ti o da lori awọn orukọ ti o ti fipamọ:",
        "Igbo": "Ndụmọdụ ezinụlọ dabere na aha ị chekwara:",
        "Hausa": "Shawarwari na iyali bisa sunayen da aka adana:",
        "Pidgin": "Family suggestion based on names wey you save:",
    },
    "comm.quick_phrases": {
        "English": "Quick phrases in", "Spanish": "Frases rápidas en",
        "French": "Phrases rapides en", "Portuguese": "Frases rápidas em",
        "Arabic": "عبارات سريعة في", "Yoruba": "Awọn gbolohun kiakia ni",
        "Igbo": "Nkebi okwu ngwa ngwa na", "Hausa": "Jimloli masu sauri a", "Pidgin": "Quick talk for",
    },
    "comm.confidence": {
        "English": "Confidence", "Spanish": "Confianza", "French": "Confiance",
        "Portuguese": "Confiança", "Arabic": "الثقة",
        "Yoruba": "Igboya", "Igbo": "Ntụkwasị obi", "Hausa": "Amincewa", "Pidgin": "Sure level",
    },

    # ========== CATEGORIES ==========
    "cat.urgent": {
        "English": "Urgent needs", "Spanish": "Necesidades urgentes", "French": "Besoins urgents",
        "Portuguese": "Necessidades urgentes", "Arabic": "احتياجات عاجلة",
        "Yoruba": "Awọn iwulo pajawiri", "Igbo": "Mkpa ngwa ngwa", "Hausa": "Bukatun gaggawa", "Pidgin": "Urgent things",
    },
    "cat.basic": {
        "English": "Basic needs", "Spanish": "Necesidades básicas", "French": "Besoins essentiels",
        "Portuguese": "Necessidades básicas", "Arabic": "الاحتياجات الأساسية",
        "Yoruba": "Awọn iwulo ipilẹ", "Igbo": "Mkpa dị mkpa", "Hausa": "Muhimman bukatu", "Pidgin": "Basic things",
    },
    "cat.feelings": {
        "English": "Feelings", "Spanish": "Sentimientos", "French": "Sentiments",
        "Portuguese": "Sentimentos", "Arabic": "المشاعر",
        "Yoruba": "Awọn imọlara", "Igbo": "Mmetụta", "Hausa": "Ji", "Pidgin": "How body dey",
    },
    "cat.requests": {
        "English": "Requests", "Spanish": "Peticiones", "French": "Demandes",
        "Portuguese": "Pedidos", "Arabic": "طلبات",
        "Yoruba": "Awọn ibeere", "Igbo": "Arịrịọ", "Hausa": "Buƙatun", "Pidgin": "Request",
    },
    "cat.family": {
        "English": "Family and social", "Spanish": "Familia y social", "French": "Famille et social",
        "Portuguese": "Família e social", "Arabic": "العائلة والاجتماعي",
        "Yoruba": "Ẹbi ati awujọ", "Igbo": "Ezinụlọ na mmekọrịta", "Hausa": "Iyali da zamantakewa", "Pidgin": "Family and friends",
    },
    "cat.food": {
        "English": "Food and drink", "Spanish": "Comida y bebida", "French": "Nourriture et boisson",
        "Portuguese": "Comida e bebida", "Arabic": "الطعام والشراب",
        "Yoruba": "Ounjẹ ati mimu", "Igbo": "Nri na ihe ọṅụṅụ", "Hausa": "Abinci da abin sha", "Pidgin": "Food and drink",
    },
    "cat.rehab": {
        "English": "Rehabilitation", "Spanish": "Rehabilitación", "French": "Réadaptation",
        "Portuguese": "Reabilitação", "Arabic": "إعادة التأهيل",
        "Yoruba": "Atunṣe", "Igbo": "Mmegharị ahụ", "Hausa": "Farfaɗowa", "Pidgin": "Body practice",
    },

    # ========== EXERCISES ==========
    "ex.title": {
        "English": "Daily exercises", "Spanish": "Ejercicios diarios",
        "French": "Exercices quotidiens", "Portuguese": "Exercícios diários",
        "Arabic": "التمارين اليومية", "Yoruba": "Awọn idaraya ojoojumọ",
        "Igbo": "Mmega ahụ kwa ụbọchị", "Hausa": "Motsa jiki na yau da kullun", "Pidgin": "Everyday exercise",
    },
    "ex.today": {
        "English": "Today", "Spanish": "Hoy", "French": "Aujourd'hui",
        "Portuguese": "Hoje", "Arabic": "اليوم",
        "Yoruba": "Loni", "Igbo": "Taa", "Hausa": "Yau", "Pidgin": "Today",
    },
    "ex.accuracy": {
        "English": "Accuracy", "Spanish": "Precisión", "French": "Précision",
        "Portuguese": "Precisão", "Arabic": "الدقة",
        "Yoruba": "Titọ", "Igbo": "Izi ezi", "Hausa": "Daidaito", "Pidgin": "Correct level",
    },
    "ex.streak": {
        "English": "Streak", "Spanish": "Racha", "French": "Série",
        "Portuguese": "Sequência", "Arabic": "السلسلة",
        "Yoruba": "Itẹlera", "Igbo": "Usoro", "Hausa": "Jere", "Pidgin": "Streak",
    },
    "ex.difficulty": {
        "English": "Difficulty", "Spanish": "Dificultad", "French": "Difficulté",
        "Portuguese": "Dificuldade", "Arabic": "الصعوبة",
        "Yoruba": "Isoro", "Igbo": "Ihe isi ike", "Hausa": "Wahala", "Pidgin": "How hard am",
    },
    "ex.word_retrieval": {
        "English": "Word retrieval", "Spanish": "Recuperación de palabras",
        "French": "Récupération de mots", "Portuguese": "Recuperação de palavras",
        "Arabic": "استرجاع الكلمات", "Yoruba": "Ibere ọrọ",
        "Igbo": "Iweghachite okwu", "Hausa": "Dawo da kalma", "Pidgin": "Find word",
    },
    "ex.sentence_building": {
        "English": "Sentence building", "Spanish": "Construcción de oraciones",
        "French": "Construction de phrases", "Portuguese": "Construção de frases",
        "Arabic": "بناء الجمل", "Yoruba": "Ikọ gbolohun",
        "Igbo": "Iwu ahịrịokwu", "Hausa": "Gina jimla", "Pidgin": "Build sentence",
    },
    "ex.cloze": {
        "English": "Fill in the blank", "Spanish": "Rellena el espacio",
        "French": "Remplir le blanc", "Portuguese": "Preencha o espaço",
        "Arabic": "املأ الفراغ", "Yoruba": "Kun aafo",
        "Igbo": "Dejuo ebe tọgbọrọ chakoo", "Hausa": "Cike fage", "Pidgin": "Fill gap",
    },
    "ex.reading": {
        "English": "Reading comprehension", "Spanish": "Comprensión lectora",
        "French": "Compréhension écrite", "Portuguese": "Compreensão de leitura",
        "Arabic": "فهم القراءة", "Yoruba": "Oye kika",
        "Igbo": "Nghọta ọgụgụ", "Hausa": "Fahimtar karatu", "Pidgin": "Read and understand",
    },
    "ex.repetition": {
        "English": "Repetition", "Spanish": "Repetición",
        "French": "Répétition", "Portuguese": "Repetição",
        "Arabic": "التكرار", "Yoruba": "Atunṣe",
        "Igbo": "Nkwugharị", "Hausa": "Maimaitawa", "Pidgin": "Repeat",
    },
    "ex.your_answer": {
        "English": "Your answer", "Spanish": "Tu respuesta", "French": "Votre réponse",
        "Portuguese": "Sua resposta", "Arabic": "إجابتك",
        "Yoruba": "Idahun rẹ", "Igbo": "Azịza gị", "Hausa": "Amsarka", "Pidgin": "Your answer",
    },
    "ex.correct": {
        "English": "Correct!", "Spanish": "¡Correcto!",
        "French": "Correct !", "Portuguese": "Correto!",
        "Arabic": "صحيح!", "Yoruba": "Titọ!",
        "Igbo": "Ziri ezi!", "Hausa": "Daidai!", "Pidgin": "You correct!",
    },
    "ex.try_hint": {
        "English": "Not quite — try a hint", "Spanish": "No del todo — prueba una pista",
        "French": "Pas tout à fait — essayez un indice", "Portuguese": "Não exatamente — tente uma dica",
        "Arabic": "ليس تماما — جرب تلميحا", "Yoruba": "Ko si — gbiyanju ìmọ̀ràn",
        "Igbo": "Ọ bụghị kpamkpam — gbalịa ntụaka", "Hausa": "Ba daidai ba — gwada alama",
        "Pidgin": "You near am — try hint",
    },

    # ========== GAMES ==========
    "games.title": {
        "English": "Games", "Spanish": "Juegos", "French": "Jeux",
        "Portuguese": "Jogos", "Arabic": "الألعاب",
        "Yoruba": "Awọn ere", "Igbo": "Egwuregwu", "Hausa": "Wasanni", "Pidgin": "Games",
    },
    "games.subtitle": {
        "English": "Fun ways to practice — earn XP and level up",
        "Spanish": "Formas divertidas de practicar — gana XP y sube de nivel",
        "French": "Façons amusantes de pratiquer — gagnez de l'XP et montez de niveau",
        "Portuguese": "Maneiras divertidas de praticar — ganhe XP e suba de nível",
        "Arabic": "طرق ممتعة للممارسة — اكسب نقاط الخبرة واصعد",
        "Yoruba": "Awọn ọna igbadun lati ṣe adaṣe — gba XP ki o dide",
        "Igbo": "Ụzọ ọmịiko iji mụta — nweta XP",
        "Hausa": "Hanyoyi masu dadi don yin aiki — sami XP",
        "Pidgin": "Nice way to practice — collect XP and level up",
    },
    "games.word_match": {
        "English": "Picture match", "Spanish": "Emparejar imágenes",
        "French": "Correspondance d'images", "Portuguese": "Combinar imagens",
        "Arabic": "مطابقة الصور", "Yoruba": "Ipele aworan",
        "Igbo": "Jikọọ foto", "Hausa": "Haɗa hoto", "Pidgin": "Match Picture",
    },
    "games.category_sort": {
        "English": "Category sort", "Spanish": "Clasificación por categoría",
        "French": "Tri par catégorie", "Portuguese": "Ordenação por categoria",
        "Arabic": "فرز الفئات", "Yoruba": "Ipin nipa ẹka",
        "Igbo": "Nhazi ụdị", "Hausa": "Tsari na nau'i", "Pidgin": "Sort by group",
    },
    "games.sentence_puzzle": {
        "English": "Sentence puzzle", "Spanish": "Rompecabezas de oraciones",
        "French": "Puzzle de phrase", "Portuguese": "Quebra-cabeça de frases",
        "Arabic": "لغز الجمل", "Yoruba": "Ère gbolohun",
        "Igbo": "Egwuregwu ahịrịokwu", "Hausa": "Wasan jimla", "Pidgin": "Sentence Puzzle",
    },
    "games.first_letter": {
        "English": "First letter challenge", "Spanish": "Desafío de primera letra",
        "French": "Défi première lettre", "Portuguese": "Desafio da primeira letra",
        "Arabic": "تحدي الحرف الأول", "Yoruba": "Ipenija lẹta akọkọ",
        "Igbo": "Aka mbụ mkpụrụedemede", "Hausa": "Ƙalubalen harafi na farko", "Pidgin": "First letter challenge",
    },
    "games.story_builder": {
        "English": "Story builder", "Spanish": "Constructor de historias",
        "French": "Constructeur d'histoires", "Portuguese": "Construtor de histórias",
        "Arabic": "منشئ القصص", "Yoruba": "Akọwe itan",
        "Igbo": "Onye na-ewu akụkọ", "Hausa": "Mai gina labari", "Pidgin": "Story Builder",
    },

    # ========== PROGRESS ==========
    "progress.title": {
        "English": "My progress", "Spanish": "Mi progreso", "French": "Mon progrès",
        "Portuguese": "Meu progresso", "Arabic": "تقدمي",
        "Yoruba": "Ilọsiwaju mi", "Igbo": "Ọganihu m", "Hausa": "Ci gabana", "Pidgin": "My progress",
    },
    "progress.total_ex": {
        "English": "Total exercises", "Spanish": "Ejercicios totales",
        "French": "Exercices totaux", "Portuguese": "Exercícios totais",
        "Arabic": "إجمالي التمارين", "Yoruba": "Lapapọ awọn idaraya",
        "Igbo": "Mmega ahụ niile", "Hausa": "Jimlar motsa jiki", "Pidgin": "All exercises",
    },
    "progress.words_recovered": {
        "English": "Words recovered", "Spanish": "Palabras recuperadas",
        "French": "Mots récupérés", "Portuguese": "Palavras recuperadas",
        "Arabic": "الكلمات المستردة", "Yoruba": "Awọn ọrọ ti a ti pada",
        "Igbo": "Okwu nwetaghachiri", "Hausa": "Kalmomin da aka dawo", "Pidgin": "Words wey you remember",
    },
    "progress.xp_earned": {
        "English": "XP earned", "Spanish": "XP ganada",
        "French": "XP gagnée", "Portuguese": "XP ganha",
        "Arabic": "النقاط المكتسبة", "Yoruba": "XP ti o ti gba",
        "Igbo": "XP enwetara", "Hausa": "XP da aka samu", "Pidgin": "XP wey you get",
    },
    "progress.to_next_level": {
        "English": "to next level", "Spanish": "para el siguiente nivel",
        "French": "au niveau suivant", "Portuguese": "para o próximo nível",
        "Arabic": "للمستوى التالي", "Yoruba": "si ipele tókàn",
        "Igbo": "gaa na ọkwa ọzọ", "Hausa": "zuwa mataki na gaba", "Pidgin": "to next level",
    },

    # ========== FAMILY ==========
    "family.title": {
        "English": "Family members", "Spanish": "Miembros de la familia",
        "French": "Membres de la famille", "Portuguese": "Membros da família",
        "Arabic": "أفراد العائلة", "Yoruba": "Awọn ọmọ ẹbi",
        "Igbo": "Ndị ezinụlọ", "Hausa": "'Yan iyali", "Pidgin": "Family people",
    },
    "family.add_member": {
        "English": "Add family member", "Spanish": "Añadir miembro familiar",
        "French": "Ajouter un membre de la famille", "Portuguese": "Adicionar membro da família",
        "Arabic": "إضافة فرد من العائلة", "Yoruba": "Fikun ọmọ ẹbi",
        "Igbo": "Tinye onye ezinụlọ", "Hausa": "Ƙara ɗan iyali", "Pidgin": "Add family person",
    },
    "family.name": {
        "English": "Name", "Spanish": "Nombre", "French": "Nom",
        "Portuguese": "Nome", "Arabic": "الاسم",
        "Yoruba": "Orukọ", "Igbo": "Aha", "Hausa": "Suna", "Pidgin": "Name",
    },
    "family.relationship": {
        "English": "Relationship", "Spanish": "Relación", "French": "Relation",
        "Portuguese": "Relação", "Arabic": "العلاقة",
        "Yoruba": "Ibatan", "Igbo": "Mmekọrịta", "Hausa": "Dangantaka", "Pidgin": "Relationship",
    },

    # ========== SETTINGS ==========
    "settings.profile": {
        "English": "Profile", "Spanish": "Perfil", "French": "Profil",
        "Portuguese": "Perfil", "Arabic": "الملف الشخصي",
        "Yoruba": "Profaili", "Igbo": "Profaịlụ", "Hausa": "Bayanan", "Pidgin": "Profile",
    },
    "settings.change_lang": {
        "English": "Change language", "Spanish": "Cambiar idioma",
        "French": "Changer de langue", "Portuguese": "Mudar idioma",
        "Arabic": "تغيير اللغة", "Yoruba": "Yi ede pada",
        "Igbo": "Gbanwee asụsụ", "Hausa": "Canza harshe", "Pidgin": "Change language",
    },
    "settings.daily_target": {
        "English": "Daily exercise target", "Spanish": "Objetivo diario",
        "French": "Objectif quotidien", "Portuguese": "Meta diária",
        "Arabic": "هدف يومي", "Yoruba": "Ibi-afẹde ojoojumọ",
        "Igbo": "Ebumnuche ụbọchị", "Hausa": "Manufar yau da kullun", "Pidgin": "Daily target",
    },
}


def t(key: str, language: str = "English") -> str:
    """
    Translate a key to the target language. Falls back to English if missing.

    Args:
        key: dot-separated translation key (e.g., "nav.communication")
        language: target language name

    Returns:
        Translated string. If key not found at all, returns the key itself
        as a visible signal that a translation is missing.
    """
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key  # loud fallback: surfaces missing keys during dev
    return entry.get(language) or entry.get("English") or key


def has_translation(key: str, language: str) -> bool:
    """Check if a specific language has a translation for a key."""
    entry = TRANSLATIONS.get(key, {})
    return language in entry
