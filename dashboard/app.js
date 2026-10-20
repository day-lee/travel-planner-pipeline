const COLORS = {
  BKK: "var(--bkk)", DAR: "var(--dar)", LAX: "var(--lax)", HKG: "var(--hkg)",
  NEG: "var(--neg)", INT: "var(--int)", SYD: "var(--syd)", ICN: "var(--icn)",
};
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
let data;
let selectedYear;
let selectedCities = [];

async function loadData() {
  const response = await fetch("data/site_data.json");
  if (!response.ok) throw new Error(`Could not load dashboard data (${response.status})`);
  data = await response.json();
  const years = [...new Set(data.school_holidays.map((holiday) => holiday.year))].sort();
  selectedYear = years[1] ?? years[0];
  document.querySelector("#year-select").innerHTML = years.map(
    (year) => `<option value="${year}">${year}</option>`,
  ).join("");
  document.querySelector("#year-select").value = selectedYear;
  document.querySelector("#year-select").addEventListener("change", (event) => {
    selectedYear = Number(event.target.value);
    renderCalendar();
  });
  document.querySelector("#clear-selections").addEventListener("click", () => {
    selectedCities = [];
    renderCityButtons();
    renderCalendar();
  });
  renderCityButtons();
  renderCalendar();
}

function cityName(cityId) {
  return data.cities.find((city) => city.city_id === cityId)?.city_name ?? cityId;
}

function monthCityName(cityId) {
  return { HKG: "HK", LAX: "LA", DAR: "DS" }[cityId] ?? cityId;
}

function toggleCity(cityId) {
  if (selectedCities.includes(cityId)) {
    selectedCities = selectedCities.filter((id) => id !== cityId);
  } else if (selectedCities.length < 3) {
    selectedCities = [...selectedCities, cityId];
  }
  renderCityButtons();
  renderCalendar();
}

function renderCityButtons() {
  const buttons = data.cities.map((city) => {
    const selected = selectedCities.includes(city.city_id);
    const disabled = !selected && selectedCities.length >= 3;
    const style = selected ? `style="background:${COLORS[city.city_id]}"` : "";
    return `<button class="city-button ${selected ? "is-selected" : ""}" ${style}
      ${disabled ? "disabled" : ""} data-city="${city.city_id}">${city.city_name}</button>`;
  }).join("");
  document.querySelector("#city-buttons").innerHTML = buttons;
  document.querySelectorAll("[data-city]").forEach((button) => {
    button.addEventListener("click", () => toggleCity(button.dataset.city));
  });
}

function dateKey(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function isoWeek(date) {
  const copy = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = copy.getUTCDay() || 7;
  copy.setUTCDate(copy.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(copy.getUTCFullYear(), 0, 1));
  return Math.ceil((((copy - yearStart) / 86400000) + 1) / 7);
}

function schoolHoliday(dateString) {
  return data.school_holidays.find((holiday) => (
    holiday.year === selectedYear
    && dateString >= holiday.start_date
    && dateString <= holiday.end_date
  ));
}

function bankHoliday(dateString) {
  return data.bank_holidays.find((holiday) => holiday.date === dateString);
}

function monthCities(month) {
  return data.city_ids.filter((cityId) => {
    const goodDates = data.weather[cityId]?.good_dates?.[String(selectedYear)] ?? [];
    return goodDates.some((dateString) => (
        new Date(`${dateString}T00:00:00Z`).getUTCMonth() === month
    ));
  });
}

function renderCalendar() {
  const calendar = document.querySelector("#calendar");
  calendar.innerHTML = MONTHS.map((month, monthIndex) => {
    const first = new Date(Date.UTC(selectedYear, monthIndex, 1));
    const daysInMonth = new Date(Date.UTC(selectedYear, monthIndex + 1, 0)).getUTCDate();
    const leading = (first.getUTCDay() + 6) % 7;
    const cells = [];
    for (let index = 0; index < leading; index += 1) cells.push('<div class="day is-outside"></div>');
    for (let day = 1; day <= daysInMonth; day += 1) {
      const key = dateKey(selectedYear, monthIndex, day);
      const holiday = schoolHoliday(key);
      const bank = bankHoliday(key);
      const tooltip = [
        bank?.name,
        holiday && `${holiday.name} · ${holiday.start_date} ~ ${holiday.end_date}`,
      ].filter(Boolean).join(" | ");
      const strips = selectedCities.map((cityId) => {
        const goodDates = data.weather[cityId]?.good_dates?.[String(selectedYear)] ?? [];
        if (!goodDates.includes(key)) return "";
        const week = Math.min(isoWeek(new Date(`${key}T00:00:00Z`)), 52);
        const score = data.weather[cityId]?.scores?.[String(week)] ?? {};
        const shoulder = Boolean(holiday);
        const percent = Math.round((score.good_day_share ?? 0) * 100);
        return `<span class="weather-strip ${shoulder ? "is-shoulder" : ""}"
          style="background:${COLORS[cityId]}" title="${cityName(cityId)} · good weather on ${percent}% of days in past years"></span>`;
      }).join("");
      cells.push(`<div class="day ${bank ? "is-bank" : ""}" ${tooltip ? `data-tooltip="${tooltip.replaceAll('"', "&quot;")}"` : ""}>
        <span class="day-number">${day}</span><div class="strips">${strips}${holiday ? '<span class="school-strip"></span>' : ""}</div>
      </div>`);
    }
    const cities = monthCities(monthIndex).map((cityId) =>
      `<button class="month-city" style="color:${COLORS[cityId]}" data-city="${cityId}">${monthCityName(cityId)}</button>`
    ).join("");
    return `<section class="month"><div class="month-title"><span class="month-name">${month}</span>
      <div class="month-cities">${cities}</div></div><div class="weekdays">${WEEKDAYS.map((day) => `<span class="weekday">${day}</span>`).join("")}</div>
      <div class="days">${cells.join("")}</div></section>`;
  }).join("");
  document.querySelectorAll(".month-city").forEach((button) => {
    button.addEventListener("click", () => toggleCity(button.dataset.city));
  });
}

loadData().catch((error) => {
  document.querySelector("#calendar").textContent = "Dashboard data could not be loaded.";
  console.error(error);
});
