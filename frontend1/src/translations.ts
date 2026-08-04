export type Language = "vi" | "en";

export const translations = {
  vi: {
    // Sidebar
    "sidebar.personalHub": "Personal Hub",
    "sidebar.knowledgeHub": "Knowledge Hub",
    "sidebar.translationStudio": "Translation Studio",
    "sidebar.languageLab": "Language Lab",
    "sidebar.systemSettings": "Cài đặt hệ thống",
    "sidebar.help": "Trợ giúp",
    "sidebar.goToChat": "Đến trang Chatbot",

    // TopBar
    "topbar.title": "IUH Portal AI",
    "topbar.accountInfo": "Thông tin tài khoản",
    "topbar.systemSettings": "Cài đặt hệ thống",
    "topbar.logout": "Đăng xuất",
    "topbar.notifications": "Thông báo",
    "topbar.apps": "Ứng dụng",
    "topbar.goToChat": "Đến trang Chatbot",

    // SettingsPage
    "settings.title": "Cài đặt hệ thống",
    "settings.subtitle": "Tùy chỉnh giao diện, ngôn ngữ và nhận thông báo học vụ IUH",
    "settings.appearance": "Giao diện & Hiển thị",
    "settings.appearanceDesc": "Chọn chủ đề giao diện phù hợp với sở thích của bạn (thay đổi ngay lập tức)",
    "settings.themeLight": "Giao diện Sáng",
    "settings.themeLightDesc": "Chuẩn sáng dễ nhìn",
    "settings.themeDark": "Giao diện Tối",
    "settings.themeDarkDesc": "Tiết kiệm mắt ban đêm",
    "settings.themeSystem": "Theo hệ thống",
    "settings.themeSystemDesc": "Đồng bộ thiết bị",
    "settings.language": "Ngôn ngữ hiển thị",
    "settings.languageDesc": "Ngôn ngữ chính sử dụng trong giao diện hệ thống",
    "settings.langVi": "Tiếng Việt (Mặc định)",
    "settings.langEn": "English (United States)",
    "settings.notifications": "Thông báo hệ thống",
    "settings.notificationsDesc": "Quản lý nhận thông báo học vụ từ trường và âm thanh thông báo",
    "settings.soundTitle": "Âm thanh thông báo",
    "settings.soundDesc": "Phát âm báo nhẹ khi hoàn thành dịch thuật hoặc thao tác xong",
    "settings.academicAlertsTitle": "Thông báo học vụ mới từ IUH",
    "settings.academicAlertsDesc": "Nhận thông báo tự động khi có quy chế mới hoặc thông báo học vụ",
    "settings.loadingSettings": "Đang tải cài đặt hệ thống...",
  },
  en: {
    // Sidebar
    "sidebar.personalHub": "Personal Hub",
    "sidebar.knowledgeHub": "Knowledge Hub",
    "sidebar.translationStudio": "Translation Studio",
    "sidebar.languageLab": "Language Lab",
    "sidebar.systemSettings": "System Settings",
    "sidebar.help": "Help",
    "sidebar.goToChat": "Go to Chatbot",

    // TopBar
    "topbar.title": "IUH Portal AI",
    "topbar.accountInfo": "Account Profile",
    "topbar.systemSettings": "System Settings",
    "topbar.logout": "Sign Out",
    "topbar.notifications": "Notifications",
    "topbar.apps": "Apps",
    "topbar.goToChat": "Go to Chatbot",

    // SettingsPage
    "settings.title": "System Settings",
    "settings.subtitle": "Customize interface, language, and receive IUH academic notifications",
    "settings.appearance": "Appearance & Display",
    "settings.appearanceDesc": "Choose an interface theme that fits your preference (changes instantly)",
    "settings.themeLight": "Light Theme",
    "settings.themeLightDesc": "Bright and clear view",
    "settings.themeDark": "Dark Theme",
    "settings.themeDarkDesc": "Easy on the eyes at night",
    "settings.themeSystem": "System Sync",
    "settings.themeSystemDesc": "Matches device settings",
    "settings.language": "Display Language",
    "settings.languageDesc": "Primary language used across the system interface",
    "settings.langVi": "Tiếng Việt (Default)",
    "settings.langEn": "English (United States)",
    "settings.notifications": "System Notifications",
    "settings.notificationsDesc": "Manage academic alerts and notification sound effects",
    "settings.soundTitle": "Notification Sound",
    "settings.soundDesc": "Play a subtle audio chime when translations or operations complete",
    "settings.academicAlertsTitle": "New IUH Academic Alerts",
    "settings.academicAlertsDesc": "Automatically receive alerts when new regulations or notices arrive",
    "settings.loadingSettings": "Loading system settings...",
  },
} as const;

export type TranslationKey = keyof typeof translations.vi;
