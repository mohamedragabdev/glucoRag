export type Language = 'en' | 'ar';
export type Theme = 'light' | 'dark' | 'system';

export interface Translations {
  appTitle: string;
  appSubtitle: string;
  appTagline: string;
  scopeWarning: string;
  scopeDisclaimer: string;
  
  // Sidebar
  conversations: string;
  newConversation: string;
  noConversations: string;
  deleteConfirm: string;
  deleteTitle: string;
  logout: string;
  clinicianRole: string;
  settings: string;
  theme: string;
  language: string;
  lightMode: string;
  darkMode: string;
  systemMode: string;

  // Auth
  signIn: string;
  signUp: string;
  registerTitle: string;
  registerSubtitle: string;
  loginTitle: string;
  loginSubtitle: string;
  fullNameLabel: string;
  fullNamePlaceholder: string;
  emailLabel: string;
  emailPlaceholder: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  confirmPasswordLabel: string;
  confirmPasswordPlaceholder: string;
  authenticating: string;
  registering: string;
  alreadyHaveAccount: string;
  needAccount: string;
  passwordMismatch: string;
  registrationFailed: string;
  loginFailed: string;

  // Chat
  assistantName: string;
  screeningAssistantBadge: string;
  emptyStateTitle: string;
  emptyStateSubtitle: string;
  samplePrompt1: string;
  samplePrompt2: string;
  samplePrompt3: string;
  samplePrompt4: string;
  composerPlaceholder: string;
  composerPendingPlaceholder: string;
  charLimitExceeded: string;
  chars: string;
  sendQuestion: string;
  footerDisclaimer: string;
  processingMessage: string;
  processingFailedTitle: string;
  processingFailedDefault: string;
  retryQuestion: string;
  evidenceSources: string;
  page: string;
}

export const translations: Record<Language, Translations> = {
  en: {
    appTitle: 'GlucoRAG',
    appSubtitle: 'T2D Screening Reference',
    appTagline: 'Evidence-Grounded Clinical Decision Support for Primary-Care Clinicians',
    scopeWarning: 'Restricted: Type 2 Diabetes Screening Only (No Diagnosis/Rx)',
    scopeDisclaimer: 'Reference tool for Type 2 Diabetes screening only. Not for diagnosis, individual treatment plans, or emergency triage.',

    conversations: 'Conversations',
    newConversation: 'New Screening Query',
    noConversations: 'No conversations yet. Start a new screening query.',
    deleteConfirm: 'Are you sure you want to delete this conversation?',
    deleteTitle: 'Delete Conversation',
    logout: 'Sign Out',
    clinicianRole: 'Primary-Care Clinician',
    settings: 'Settings',
    theme: 'Theme',
    language: 'Language',
    lightMode: 'Light',
    darkMode: 'Dark',
    systemMode: 'System',

    signIn: 'Sign In',
    signUp: 'Register Account',
    registerTitle: 'Clinician Registration',
    registerSubtitle: 'Create an account to access GlucoRAG screening reference evidence',
    loginTitle: 'GlucoRAG',
    loginSubtitle: 'Type 2 Diabetes Screening Decision Support for Primary-Care Clinicians',
    fullNameLabel: 'Full Name (e.g. Dr. Jane Smith)',
    fullNamePlaceholder: 'Dr. Jane Smith',
    emailLabel: 'Clinician Email Address',
    emailPlaceholder: 'clinician@hospital.org',
    passwordLabel: 'Password',
    passwordPlaceholder: '••••••••',
    confirmPasswordLabel: 'Confirm Password',
    confirmPasswordPlaceholder: '••••••••',
    authenticating: 'Authenticating...',
    registering: 'Creating Account...',
    alreadyHaveAccount: 'Already have a clinician account? Sign in',
    needAccount: 'Need a clinician account? Register here',
    passwordMismatch: 'Password confirmation does not match.',
    registrationFailed: 'Registration failed. Please check the inputs.',
    loginFailed: 'Invalid credentials. Please verify your email and password.',

    assistantName: 'GlucoRAG',
    screeningAssistantBadge: 'GlucoRAG Reference',
    emptyStateTitle: 'GlucoRAG Decision Support',
    emptyStateSubtitle: 'Ask guideline-based Type 2 Diabetes screening questions. Answers are verified against ingested clinical guidelines with verified citations.',
    samplePrompt1: 'What is the recommended universal screening age for T2D according to ADA guidelines?',
    samplePrompt2: 'What risk factors warrant diabetes screening in adults under age 35?',
    samplePrompt3: 'What are the cutoff values for FPG, A1C, and 2-h OGTT in screening?',
    samplePrompt4: 'If initial screening test results are normal, what is the recommended repeat interval?',
    composerPlaceholder: 'Ask a Type 2 Diabetes screening question (e.g., ADA age thresholds, FPG/A1C criteria, screening intervals)...',
    composerPendingPlaceholder: 'Processing screening query... Please wait.',
    charLimitExceeded: 'Exceeds 2000 character maximum limit',
    chars: 'chars',
    sendQuestion: 'Send Question',
    footerDisclaimer: 'Clinical reference tool only. Not for diagnosis, individual treatment plans, or emergency care.',
    processingMessage: 'Retrieving screening evidence & synthesizing answer...',
    processingFailedTitle: 'Processing Failed',
    processingFailedDefault: "We couldn't process your question right now. Please try again.",
    retryQuestion: 'Retry Question',
    evidenceSources: 'Evidence Sources & Citations',
    page: 'Page',
  },
  ar: {
    appTitle: 'جلوكوراج (GlucoRAG)',
    appSubtitle: 'مرجع فحص السكري من النوع الثاني',
    appTagline: 'دعم القرار الإكلينيكي المبني على الأدلة لأطباء الرعاية الأولية',
    scopeWarning: 'مخصص لفحص السكري من النوع الثاني فقط (ليس للتشخيص أو العلاج)',
    scopeDisclaimer: 'أداة مرجعية لفحص السكري من النوع الثاني فقط. ليست للتشخيص الطبي أو وضع الخطط العلاجية الفردية أو الطوارئ.',

    conversations: 'المحادثات',
    newConversation: 'استفسار فحص جديد',
    noConversations: 'لا توجد محادثات سابقة. ابدأ استفسار فحص جديد.',
    deleteConfirm: 'هل أنت متأكد من رغبتك في حذف هذه المحادثة؟',
    deleteTitle: 'حذف المحادثة',
    logout: 'تسجيل الخروج',
    clinicianRole: 'طبيب رعاية أولية',
    settings: 'الإعدادات',
    theme: 'المظهر',
    language: 'اللغة',
    lightMode: 'فاتح',
    darkMode: 'داكن',
    systemMode: 'تلقائي',

    signIn: 'تسجيل الدخول',
    signUp: 'إنشاء حساب جديد',
    registerTitle: 'تسجيل الأطباء والممارسين',
    registerSubtitle: 'أنشئ حسابك للوصول إلى أدلة فحص السكري عبر جلوكوراج (GlucoRAG)',
    loginTitle: 'جلوكوراج (GlucoRAG)',
    loginSubtitle: 'دعم قرار فحص السكري من النوع الثاني لأطباء الرعاية الأولية',
    fullNameLabel: 'الاسم الكامل (مثال: د. سارة أحمد)',
    fullNamePlaceholder: 'د. سارة أحمد',
    emailLabel: 'البريد الإلكتروني المهني',
    emailPlaceholder: 'clinician@hospital.org',
    passwordLabel: 'كلمة المرور',
    passwordPlaceholder: '••••••••',
    confirmPasswordLabel: 'تأكيد كلمة المرور',
    confirmPasswordPlaceholder: '••••••••',
    authenticating: 'جاري التحقق...',
    registering: 'جاري إنشاء الحساب...',
    alreadyHaveAccount: 'لديك حساب بالفعل؟ تسجيل الدخول',
    needAccount: 'ليس لديك حساب؟ سجّل الآن',
    passwordMismatch: 'تأكيد كلمة المرور غير متطابق.',
    registrationFailed: 'فشل إنشاء الحساب. يرجى التحقق من البيانات المدخلة.',
    loginFailed: 'بيانات الدخول غير صحيحة. يرجى التحقق من البريد وكلمة المرور.',

    assistantName: 'جلوكوراج (GlucoRAG)',
    screeningAssistantBadge: 'مرجع جلوكوراج',
    emptyStateTitle: 'مساعد فحص السكري جلوكوراج (GlucoRAG)',
    emptyStateSubtitle: 'اطرح أسئلة فحص السكري المعتمدة على الإرشادات الطبية. كل إجابة يتم التحقق منها استناداً إلى الأدلة الإكلينيكية المعتمدة مع توثيق المصادر.',
    samplePrompt1: 'ما هو السن الموصى به للفحص الشامل للسكري من النوع الثاني وفقاً لإرشادات ADA؟',
    samplePrompt2: 'ما هي عوامل الخطورة التي تستوجب فحص السكري لدى البالغين دون سن 35؟',
    samplePrompt3: 'ما هي القيم المرجعية لتحاليل سكر الصائم والتراكمي واختبار تحمل الجلوكوز؟',
    samplePrompt4: 'إذا كانت نتائج الفحص المبدئي طبيعية، فما هي الفترة الموصى بها لإعادة الفحص؟',
    composerPlaceholder: 'اطرح سؤالاً حول فحص السكري من النوع الثاني (مثل معايير العمر، قراءات السكر، فترات الفحص)...',
    composerPendingPlaceholder: 'جاري معالجة استفسار الفحص... يرجى الانتظار.',
    charLimitExceeded: 'تم تجاوز الحد الأقصى المسموح به (2000 حرف)',
    chars: 'حرف',
    sendQuestion: 'إرسال السؤال',
    footerDisclaimer: 'أداة مرجعية إكلينيكية فقط. ليست للتشخيص الطبي أو العلاج أو الرعاية الطارئة.',
    processingMessage: 'جاري استرجاع الأدلة الإكلينيكية وصياغة الإجابة الموثقة...',
    processingFailedTitle: 'فشلت المعالجة',
    processingFailedDefault: 'تعذر معالجة استفسارك حالياً. يرجى إعادة المحاولة.',
    retryQuestion: 'إعادة محاولة السؤال',
    evidenceSources: 'المصادر المرجعية والاستشهادات',
    page: 'صفحة',
  },
};
