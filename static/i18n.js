// ═══════════════════════════════════════════════════════════════════════════════
//  INTERNATIONALIZATION (EN / RU)
// ═══════════════════════════════════════════════════════════════════════════════
const TRANSLATIONS = {
  en: {
    // Header
    title: "Tashkent Restaurant Market Tracker",
    subtitle: "Competitive intelligence for restaurant holdings &mdash; real data only",
    // Tabs
    tab_menu: "Menu Management",
    tab_price: "Price Comparison",
    tab_market: "Market Analytics",
    tab_restaurants: "Restaurants",
    // Coverage cards
    cov_tracked: "Restaurants Tracked",
    cov_with: "With Menu Data",
    cov_without: "Missing Menu Data",
    cov_items: "Total Items Entered",
    // Add menu item
    add_item: "Add Menu Item",
    add_item_hint: "Enter prices from actual menus you've collected from restaurant visits.",
    lbl_restaurant: "Restaurant",
    lbl_category: "Category",
    lbl_dish: "Dish Name",
    lbl_price: "Price (UZS)",
    lbl_desc: "Description (optional)",
    lbl_collected_by: "Collected By",
    lbl_date: "Collection Date",
    btn_add_item: "Add Item",
    ph_category: "e.g. Salads, Mains, Desserts",
    ph_dish: "e.g. Caesar Salad",
    ph_desc: "Romaine, parmesan, croutons...",
    ph_your_name: "Your name",
    // OCR
    ocr_title: "Upload Menu Photo / PDF (OCR)",
    ocr_hint: "Upload a photo or PDF of a restaurant menu. The system will read it automatically and extract dishes and prices.",
    lbl_menu_file: "Menu File (photo or PDF)",
    btn_scan: "Scan Menu",
    ocr_parsed: "Parsed Items — review, edit, and save",
    th_include: "Include",
    btn_save_selected: "Save Selected Items",
    ocr_raw: "View raw OCR text",
    // CSV
    csv_title: "Bulk CSV Upload",
    csv_hint: "Upload a CSV file with columns:",
    lbl_csv_file: "CSV File",
    btn_upload_csv: "Upload CSV",
    csv_example: "CSV format example",
    // Browse menu
    browse_title: "Browse / Edit Restaurant Menu",
    lbl_select_rest: "Select Restaurant",
    opt_choose: "— Choose —",
    // Price changes
    price_changes: "Recent Price Changes",
    th_date: "Date",
    th_dish: "Dish",
    th_old_price: "Old Price",
    th_new_price: "New Price",
    th_change: "Change",
    th_by: "By",
    // Price comparison
    pc_hint: "Compare actual collected prices across restaurants. Only shows data your team has entered.",
    opt_all: "All",
    opt_select_dish: "— Select —",
    btn_compare: "Compare",
    pc_coverage: "Data Coverage",
    pc_avg: "Market Average",
    pc_min: "Cheapest",
    pc_max: "Most Expensive",
    pc_breakdown: "Detailed Breakdown",
    th_segment: "Segment",
    th_vs_avg: "vs Market Avg",
    th_collected: "Collected",
    pc_empty: 'No price data yet for this dish. Go to <strong>Menu Management</strong> to enter prices.',
    // Market analytics
    market_empty: 'Enter menu data in <strong>Menu Management</strong> first to see analytics.',
    chart_segment: "Avg Menu Price by Segment",
    chart_district: "Restaurants by District",
    ranking_title: "Restaurant Data Completeness",
    th_cuisine: "Cuisine",
    th_district: "District",
    th_items: "Items Entered",
    th_avg_price: "Avg Price",
    seg_breakdown: "Segment Breakdown",
    dist_breakdown: "District Breakdown",
    th_restaurants: "Restaurants",
    th_avg_menu: "Avg Menu Price",
    // Restaurants tab
    add_rest: "Add New Restaurant",
    lbl_name: "Name",
    lbl_address: "Address",
    lbl_phone: "Phone",
    lbl_bill_min: "Avg Bill Min (UZS)",
    lbl_bill_max: "Avg Bill Max (UZS)",
    btn_add_rest: "Add Restaurant",
    th_bill_range: "Bill Range (UZS)",
    ph_rest_name: "e.g. Novikov Cafe",
    ph_cuisine: "e.g. Italian / Mediterranean",
    ph_address: "e.g. Ukchi St 1A",
    ph_district: "e.g. Shaykhantakhur",
    // Footer
    footer: "Tashkent Restaurant Market Tracker &mdash; All prices are manually collected from real menus",
    // Dynamic JS strings
    msg_item_added: "Item added!",
    msg_no_changes: "No price changes yet",
    msg_select_csv: "Select a CSV file first",
    msg_uploaded: "Uploaded: {0} items added.",
    msg_skipped: "Skipped: {0}",
    msg_no_menu: "No menu items entered for this restaurant yet. Add items above or upload a CSV.",
    msg_scanning: "Scanning menu... this may take a moment.",
    msg_found_items: "Found {0} items. Review below and save.",
    msg_upload_fail: "Upload failed: {0}",
    msg_no_selected: "No items selected",
    msg_saved_items: "Saved {0} items!",
    msg_rest_added: "{0} added!",
    msg_confirm_del: 'Remove "{0}" and all its menu data? This cannot be undone.',
    msg_select_photo: "Select a photo or PDF first",
    btn_save: "Save",
    btn_saved: "Saved!",
    btn_del: "Del",
    btn_remove: "Remove",
    lbl_none: "none",
    // Browse table headers
    th_actions: "Actions",
    // Chart label
    chart_price_label: "Price (UZS)",
    chart_avg_label: "Avg Menu Price",
    // Price comparison chart
    pc_chart_title: "{0} — Price by Restaurant",
    // Avg suffix
    avg_suffix: "Avg",
  },

  ru: {
    // Header
    title: "Трекер ресторанного рынка Ташкента",
    subtitle: "Конкурентная аналитика для ресторанных холдингов &mdash; только реальные данные",
    // Tabs
    tab_menu: "Управление меню",
    tab_price: "Сравнение цен",
    tab_market: "Аналитика рынка",
    tab_restaurants: "Рестораны",
    // Coverage cards
    cov_tracked: "Отслеживается ресторанов",
    cov_with: "С данными меню",
    cov_without: "Без данных меню",
    cov_items: "Всего позиций",
    // Add menu item
    add_item: "Добавить позицию меню",
    add_item_hint: "Вводите цены из реальных меню, собранных при посещении ресторанов.",
    lbl_restaurant: "Ресторан",
    lbl_category: "Категория",
    lbl_dish: "Название блюда",
    lbl_price: "Цена (UZS)",
    lbl_desc: "Описание (необязательно)",
    lbl_collected_by: "Кто собрал",
    lbl_date: "Дата сбора",
    btn_add_item: "Добавить",
    ph_category: "напр. Салаты, Горячее, Десерты",
    ph_dish: "напр. Салат Цезарь",
    ph_desc: "Романо, пармезан, сухарики...",
    ph_your_name: "Ваше имя",
    // OCR
    ocr_title: "Загрузить фото / PDF меню (OCR)",
    ocr_hint: "Загрузите фото или PDF меню ресторана. Система автоматически считает его и извлечёт блюда и цены.",
    lbl_menu_file: "Файл меню (фото или PDF)",
    btn_scan: "Сканировать меню",
    ocr_parsed: "Найденные позиции — проверьте, отредактируйте и сохраните",
    th_include: "Включить",
    btn_save_selected: "Сохранить выбранные",
    ocr_raw: "Показать распознанный текст",
    // CSV
    csv_title: "Загрузка CSV",
    csv_hint: "Загрузите CSV-файл с колонками:",
    lbl_csv_file: "CSV-файл",
    btn_upload_csv: "Загрузить CSV",
    csv_example: "Пример формата CSV",
    // Browse menu
    browse_title: "Просмотр / Редактирование меню",
    lbl_select_rest: "Выберите ресторан",
    opt_choose: "— Выберите —",
    // Price changes
    price_changes: "Последние изменения цен",
    th_date: "Дата",
    th_dish: "Блюдо",
    th_old_price: "Старая цена",
    th_new_price: "Новая цена",
    th_change: "Изменение",
    th_by: "Кто",
    // Price comparison
    pc_hint: "Сравнивайте реальные собранные цены в разных ресторанах. Показываются только введённые вашей командой данные.",
    opt_all: "Все",
    opt_select_dish: "— Выберите —",
    btn_compare: "Сравнить",
    pc_coverage: "Покрытие данных",
    pc_avg: "Средняя по рынку",
    pc_min: "Самая низкая",
    pc_max: "Самая высокая",
    pc_breakdown: "Подробная разбивка",
    th_segment: "Сегмент",
    th_vs_avg: "vs Средняя",
    th_collected: "Собрано",
    pc_empty: 'Нет данных по этому блюду. Перейдите в <strong>Управление меню</strong> для ввода цен.',
    // Market analytics
    market_empty: 'Сначала введите данные меню в разделе <strong>Управление меню</strong>.',
    chart_segment: "Средняя цена по сегменту",
    chart_district: "Рестораны по районам",
    ranking_title: "Полнота данных по ресторанам",
    th_cuisine: "Кухня",
    th_district: "Район",
    th_items: "Позиций введено",
    th_avg_price: "Средняя цена",
    seg_breakdown: "Разбивка по сегментам",
    dist_breakdown: "Разбивка по районам",
    th_restaurants: "Рестораны",
    th_avg_menu: "Средняя цена меню",
    // Restaurants tab
    add_rest: "Добавить ресторан",
    lbl_name: "Название",
    lbl_address: "Адрес",
    lbl_phone: "Телефон",
    lbl_bill_min: "Мин. средний чек (UZS)",
    lbl_bill_max: "Макс. средний чек (UZS)",
    btn_add_rest: "Добавить ресторан",
    th_bill_range: "Средний чек (UZS)",
    ph_rest_name: "напр. Novikov Cafe",
    ph_cuisine: "напр. Итальянская / Средиземноморская",
    ph_address: "напр. ул. Укчи 1А",
    ph_district: "напр. Шайхантахур",
    // Footer
    footer: "Трекер ресторанного рынка Ташкента &mdash; Все цены собраны вручную из реальных меню",
    // Dynamic JS strings
    msg_item_added: "Позиция добавлена!",
    msg_no_changes: "Изменений цен пока нет",
    msg_select_csv: "Сначала выберите CSV-файл",
    msg_uploaded: "Загружено: {0} позиций добавлено.",
    msg_skipped: "Пропущено: {0}",
    msg_no_menu: "Для этого ресторана ещё нет данных меню. Добавьте позиции выше или загрузите CSV.",
    msg_scanning: "Сканирование меню... подождите.",
    msg_found_items: "Найдено {0} позиций. Проверьте и сохраните.",
    msg_upload_fail: "Ошибка загрузки: {0}",
    msg_no_selected: "Ничего не выбрано",
    msg_saved_items: "Сохранено {0} позиций!",
    msg_rest_added: "{0} добавлен!",
    msg_confirm_del: 'Удалить "{0}" и все данные меню? Это действие нельзя отменить.',
    msg_select_photo: "Сначала выберите фото или PDF",
    btn_save: "Сохр.",
    btn_saved: "Готово!",
    btn_del: "Удал.",
    btn_remove: "Удалить",
    lbl_none: "нет",
    // Browse table headers
    th_actions: "Действия",
    // Chart labels
    chart_price_label: "Цена (UZS)",
    chart_avg_label: "Ср. цена меню",
    // Price comparison chart
    pc_chart_title: "{0} — Цена по ресторанам",
    // Avg suffix
    avg_suffix: "Ср.",
  }
};

let currentLang = localStorage.getItem("lang") || "en";

function t(key, ...args) {
  let s = (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) || TRANSLATIONS.en[key] || key;
  args.forEach((a, i) => { s = s.replace(`{${i}}`, a); });
  return s;
}

function applyLanguage() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const val = t(key);
    if (val) el.innerHTML = val;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    const val = t(key);
    if (val) el.placeholder = val;
  });
  document.getElementById("langBtn").textContent = currentLang === "en" ? "RU" : "EN";
  document.title = t("title");
}

function toggleLang() {
  currentLang = currentLang === "en" ? "ru" : "en";
  localStorage.setItem("lang", currentLang);
  applyLanguage();
  // Re-render dynamic content for the active tab
  const activeTab = document.querySelector(".tab.active");
  if (activeTab) {
    const tab = activeTab.dataset.tab;
    if (tab === "menu-mgmt") loadMenuManagement();
    if (tab === "price-compare") loadPriceCompareTab();
    if (tab === "market") loadMarketAnalytics();
    if (tab === "restaurants") renderRestaurantTable();
  }
}
