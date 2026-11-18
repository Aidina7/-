/* Сайт баптаулары. */
window.SITE = {
  // Google Apps Script веб-қосымшасының мекенжайы.
  API_URL: "https://script.google.com/macros/s/AKfycbwU8vHndyJqHQeikg4HTOVHBlU0GRrgqMg6TesG5_PUIjnLHsaDotScOS91tMX3Vvs/exec",

  GROUPS: ["ИС 3-1"],
  QUIZ_SIZE: 10,

  // тақырып коды -> атауы (тест нәтижелері осы кодпен сақталады)
  TOPICS: {
    inventory: "Активтер мен қызметтердің инвентаризациясы",
    licenses: "Лицензиялар мен бағдарламаларды бақылау",
    anomaly: "Желілік аномалияларды анықтау",
    sla: "Қызмет көрсету сапасын тексеру (SLA)"
  },

  // Тақырыптарға бейне: YouTube сілтемесі немесе files/ қалтасындағы mp4.
  VIDEOS: { inventory: "", licenses: "", anomaly: "", sla: "" }
};
