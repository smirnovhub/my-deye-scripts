const pageUpdateInterval = 7500;
const lastButtonName = 'last_button';

var totalSeconds = 0;
var updateTimer = null;
var secondsTimer = null;
var updating = false;
var processing = false;
var writing = false;

document.addEventListener('DOMContentLoaded', () => {
  onLoad();
});

function onLoad() {
  let defaultTabs = [];

  const lastButtonId = sessionStorage.getItem(lastButtonName);

  if (!isEmpty(lastButtonId)) {
    const el = document.getElementById(lastButtonId);
    if (el) {
      defaultTabs = [el];
    }
  }

  if (defaultTabs.length === 0) {
    defaultTabs = Array.from(document.getElementsByClassName("default_open"));
  }

  // If at least one element exists, click the first one
  if (defaultTabs.length > 0) {
    const target = defaultTabs[0];

    if (target.id) {
      sessionStorage.setItem(lastButtonName, target.id);
    }

    target.click(); // simulate click on the first default tab
    target.scrollIntoView({ behavior: "auto", inline: "center" });
  }

  const spinners = document.getElementsByClassName("remote_data_with_spinner");
  for (let i = 0; i < spinners.length; i++)
    addSpinner(spinners[i].id);

  update();
  startUpdateTimer();

  const menu = document.getElementById("menu");
  const scrollLeftBtn = document.getElementById("scroll-left");
  const scrollRightBtn = document.getElementById("scroll-right");

  function updateScrollButtons() {
    // Check if the content is wider than the visible area
    const hasScroll = menu.scrollWidth > menu.clientWidth;
    if (hasScroll) {
      // Show both buttons if scrolling is possible at all
      scrollLeftBtn.style.opacity = "1";
      scrollLeftBtn.style.pointerEvents = "auto";
      scrollRightBtn.style.opacity = "1";
      scrollRightBtn.style.pointerEvents = "auto";
    } else {
      // Hide both buttons if everything fits on the screen
      scrollLeftBtn.style.opacity = "0";
      scrollLeftBtn.style.pointerEvents = "none";
      scrollRightBtn.style.opacity = "0";
      scrollRightBtn.style.pointerEvents = "none";
    }
  }

  scrollLeftBtn.addEventListener("click", () => {
    smoothScrollTo(menu, 0, 500);
  });

  scrollRightBtn.addEventListener("click", () => {
    const maxScroll = menu.scrollWidth - menu.clientWidth;
    smoothScrollTo(menu, maxScroll, 500);
  });

  window.addEventListener("resize", updateScrollButtons);

  updateScrollButtons();

  window.scrollTo(0, 0);
}

/**
 * Smoothly scrolls an element to a specific horizontal position with custom duration.
 * @param {HTMLElement} element - The container to scroll.
 * @param {number} targetLeft - The target scrollLeft position.
 * @param {number} duration - Animation duration in milliseconds.
 */
function smoothScrollTo(element, targetLeft, duration) {
  const startLeft = element.scrollLeft;
  const change = targetLeft - startLeft;
  const startTime = performance.now();

  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    const easing = progress < 0.5 ?
      4 * progress * progress * progress :
      1 - Math.pow(-2 * progress + 2, 3) / 2;

    element.scrollLeft = startLeft + change * easing;

    if (elapsed < duration) {
      requestAnimationFrame(animate);
    }
  }

  requestAnimationFrame(animate);
}

function interpolateColor(color1, color2, percent) {
  // Convert the hex colors to RGB values
  const r1 = parseInt(color1.substring(1, 3), 16);
  const g1 = parseInt(color1.substring(3, 5), 16);
  const b1 = parseInt(color1.substring(5, 7), 16);

  const r2 = parseInt(color2.substring(1, 3), 16);
  const g2 = parseInt(color2.substring(3, 5), 16);
  const b2 = parseInt(color2.substring(5, 7), 16);

  // Interpolate the RGB values
  const r = Math.round(r1 + (r2 - r1) * percent);
  const g = Math.round(g1 + (g2 - g1) * percent);
  const b = Math.round(b1 + (b2 - b1) * percent);

  // Convert the interpolated RGB values back to a hex color
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

function setGrayscale(grayscale) {
  document.body.style.filter = "grayscale(" + grayscale + ")";
  document.body.style.background = interpolateColor('#ffffff', '#dddddd', grayscale);

  const menus = document.getElementsByClassName("scrollmenu");
  for (let i = 0; i < menus.length; i++)
    menus[i].style.background = interpolateColor('#ffffff', '#dddddd', grayscale);
}

function updateTime() {
  totalSeconds++;

  var grayscale = 0;
  const totalMilliseconds = totalSeconds * 1000;

  if (totalMilliseconds > pageUpdateInterval) {
    grayscale = (totalMilliseconds - pageUpdateInterval) / pageUpdateInterval;
    if (grayscale > 1.0)
      grayscale = 1.0;
  }

  setGrayscale(grayscale);

  const counters = document.getElementsByClassName("counter");
  for (let i = 0; i < counters.length; i++)
    counters[i].innerHTML = `Last update: ${totalSeconds} seconds ago`;
}

function stopUpdateTimer() {
  if (updateTimer) {
    clearInterval(updateTimer);
    updateTimer = null;
  }
}

function startUpdateTimer() {
  stopUpdateTimer();
  updateTimer = setInterval(update, pageUpdateInterval);
}

function resetSecondsTimer() {
  totalSeconds = 0;

  const counters = document.getElementsByClassName("counter");
  for (let i = 0; i < counters.length; i++)
    counters[i].innerHTML = `Last update: ${totalSeconds} seconds ago`;

  setGrayscale(0);

  if (secondsTimer)
    clearInterval(secondsTimer);

  secondsTimer = setInterval(updateTime, 1000);
}

function updateAllFields(result) {
  if (!result) {
    return;
  }

  document.getElementById('error_field').innerHTML = '';
  document.getElementById('callstack_field').innerHTML = '';

  const groups = [
    { class: "remote_data_with_spinner", field_id: "remote_field", apply: (el, v) => el.innerHTML = v },
    { class: "remote_data", field_id: "remote_field", apply: (el, v) => el.innerHTML = v },
    { class: "tablink", field_id: "remote_color", apply: (el, v) => el.style.backgroundColor = v },
  ];

  for (const group of groups) {
    const elements = document.getElementsByClassName(group.class);

    for (const el of elements) {
      const key = el.dataset[group.field_id];
      const val = result[key];

      if (!isEmpty(val))
        group.apply(el, val);
    }
  }
}

function update() {
  if (updating || processing || writing) {
    return;
  }

  updating = true;

  JsHttpRequest.query
    (
      'back.php',
      {
        'command': 'read_registers'
      },

      function (result, errors) {
        try {
          if (!writing) {
            updateAllFields(result);
            resetSecondsTimer();
          }
        } finally {
          updating = false;
        }
      },
      true
    );
}

function sendCommand(command, field_id) {
  if (processing || writing) {
    return;
  }

  processing = true;

  addSpinner(field_id);

  JsHttpRequest.query
    (
      'back.php',
      {
        'command': command
      },

      function (result, errors) {
        try {
          updateAllFields(result);
          resetSecondsTimer();
        } finally {
          processing = false;
        }
      },
      true
    );
}

function get_forecast_by_percent(field_id) {
  sendCommand('get_forecast_by_percent', field_id);
}

function get_forecast_by_time(field_id) {
  sendCommand('get_forecast_by_time', field_id);
}

function update_scripts(field_id) {
  sendCommand('update_scripts', field_id);
}

function write_register(field_id,
  content_field_id,
  register_name,
  register_value,
  need_confirmation = false,
) {
  if (writing) {
    return;
  }

  if (need_confirmation && !confirm('Are you sure?')) {
    return;
  }

  writing = true;

  stopUpdateTimer();
  addSpinner(field_id);
  addSpinner(content_field_id);

  JsHttpRequest.query
    (
      'back.php',
      {
        'command': 'write_register',
        'register_name': register_name,
        'register_value': register_value,
      },

      function (result, errors) {
        try {
          updateAllFields(result);
          resetSecondsTimer();
          startUpdateTimer();
        } finally {
          writing = false;
        }
      },
      true
    );
}

function addSpinner(field_id) {
  const spinnerHTML = '<div class="spinner"></div>';
  const matches = document.querySelectorAll(`[id="${field_id}"]`);
  for (let i = 0; i < matches.length; i++) {
    matches[i].innerHTML = spinnerHTML;
  }
}

function openPage(pageName, buttonName, doScroll = false) {
  const tabContent = document.getElementsByClassName("tabcontent");
  for (let i = 0; i < tabContent.length; i++) {
    tabContent[i].style.display = "none";
  }

  const tabLinks = document.getElementsByClassName("tablink");
  for (let i = 0; i < tabLinks.length; i++) {
    tabLinks[i].style.boxShadow = "";
  }

  const temps = document.getElementsByClassName("temporary_data");
  for (let i = 0; i < temps.length; i++)
    temps[i].innerHTML = "";

  document.getElementById(pageName).style.display = "block";

  const target = document.getElementById(buttonName);
  target.style.boxShadow = "5px 5px 5px rgba(0, 0, 0, 0.5)";

  if (doScroll) {
    target.scrollIntoView({ behavior: "smooth", inline: "center" });
  } else {
    target.scrollIntoView({ behavior: "smooth", inline: "nearest" });
  }

  window.scrollTo(0, 0);
  sessionStorage.setItem(lastButtonName, buttonName);
}

function isEmpty(value) {
  return (value == null || (typeof value === "string" && value.trim().length === 0));
}

function openInNewTab(url) {
  window.open(url, '_blank').focus();
}
